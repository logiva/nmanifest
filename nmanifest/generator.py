import argparse
import os
import sys

import jinja2
import oyaml as yaml
from dict_recursive_update import recursive_update
from jinja2 import FileSystemLoader


######### yaml print null's as ''
def represent_none(self, _):
    return self.represent_scalar('tag:yaml.org,2002:null', '')


yaml.add_representer(type(None), represent_none)


#########

def _get_manifest_coords(manifest: dict) -> tuple:
    """Create a tuple with the manifest (kind, namespace, name)"""
    kind = manifest.get('kind')
    namespace = manifest.get('metadata').get('namespace')
    name = manifest.get('metadata').get('name')
    return (kind, namespace, name)


class EnvironmentGenerator:
    """Given the path to an environment instance containing generatorconfigs and templates,
    this class will output rendered templates to sys.stdout."""

    def __init__(self, envdir):
        self.envdir = envdir
        self._generatorconfigs = None
        self._templatesets = None

    def _is_generatorconfig(self, manifest: dict):
        """Check if this yaml looks loke a generatorconfig"""
        return 'generatorconfigversion' in manifest

    def _get_generatorconfigs(self) -> list:
        """Load all generatorconfig definitions into memory"""
        if not self._generatorconfigs:
            self._generatorconfigs = []
            for root, dirs, files in os.walk(os.path.join(self.envdir, 'generatorconfigs')):
                for file in (os.path.join(root, f) for f in files if f.endswith('.yaml') or f.endswith('.yml')):
                    # print("parsing generatorconfig file ", file, stream)
                    with open(file, 'r') as fileh:
                        for manifest in yaml.load_all(fileh, Loader=yaml.Loader):
                            if self._is_generatorconfig(manifest):
                                self._generatorconfigs.append(manifest)
        return self._generatorconfigs

    def _generatorconfig_byid(self, id: str) -> dict:
        """Lookup a generator config by its optional id"""
        found = [g for g in self._get_generatorconfigs() if g.get('id', None) == id]
        if len(found) > 1:
            raise Exception("Found multiple generatorconfigs with id ='{}'".format(id))
        return found[0] if found else None

    def _get_resulting_substitutionparameters(self, generatorconfig: dict) -> dict:
        """Import substitutionparameters and include parameters from referenced generatorconfigs"""
        result = {}
        # depth first
        for import_id in generatorconfig.get('import_substitution_parameters', []):
            import_from = self._generatorconfig_byid(import_id)
            if import_from:
                recursive_update(result, self._get_resulting_substitutionparameters(import_from))
        # generatorconfig can override imported substitutionparameters
        substitution_parameters = generatorconfig.get("substitution_parameters", {})
        return recursive_update(result, substitution_parameters)

    def _get_templatesets(self) -> dict:
        """Load the sets of jinja2 templates into memory"""
        if not self._templatesets:
            self._templatesets = {}
            for templatesetdir_name in os.listdir(os.path.join(self.envdir, "templates")):
                templatesetdir = os.path.join(self.envdir, "templates", templatesetdir_name)
                if os.path.isdir(templatesetdir):
                    self._templatesets[templatesetdir_name] = jinja2.Environment(
                        loader=FileSystemLoader(templatesetdir))
        return self._templatesets

    def _jinja2_render(self, generatorconfig: dict) -> dict:
        result = {}

        resulting_parameters = self._get_resulting_substitutionparameters(generatorconfig)

        templateset_id = generatorconfig['templateset']
        templateset = self._get_templatesets().get(templateset_id, None)
        if not templateset:
            raise Exception("Templateset '{}' referenced by configgenerator not found".format(templateset_id))

        for template_name in templateset.list_templates():
            template = templateset.get_template(template_name)
            rendered = template.render(resulting_parameters)
            for manifest in yaml.load_all(rendered, Loader=yaml.Loader):
                # k8s coordinates
                result[_get_manifest_coords(manifest)] = manifest
        return result

    def _apply_yaml_overrides(self, generatorconfig: dict, jinja2_rendered_manifests: dict):
        for override in generatorconfig.get("overrides", []) or []:
            override_values = override.get('values', None)
            if not override_values:
                raise Exception("Override section must contain a values section")

            manifest_to_override = None

            # Check if specific coordinates to target manifest is provided
            if 'manifest' in override:
                manifest = override.get('manifest')
                # k8s coordinates
                manifest_coords = (manifest['kind'], manifest['namespace'], manifest['name'])
                manifest_to_override = jinja2_rendered_manifests.get(manifest_coords, None)
                if not manifest_to_override:
                    raise Exception("Rendered manifest with coords {} not found".format(manifest_coords))

            # If there is just 1 manifest, we don't need coordinates
            elif len(jinja2_rendered_manifests) == 1:
                manifest_to_override = list(jinja2_rendered_manifests.values())[0]

            elif len(jinja2_rendered_manifests) > 1:
                raise Exception("override section does not specify manifest coordinates and manifest count > 1")

            recursive_update(manifest_to_override, override_values)

    def render(self):
        for generatorconfig in self._get_generatorconfigs():
            rendered_manifests = self._jinja2_render(generatorconfig)
            self._apply_yaml_overrides(generatorconfig, rendered_manifests)

            for manifest in rendered_manifests.values():
                print("---", file=sys.stdout)
                yaml.dump(manifest, sys.stdout, Dumper=yaml.Dumper)


def _argparser():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("envdir",
                           help="""Environment directory to render. 
                           Should contain a number of directories,
                           each with the subdirectories (generatorconfigs, templates)"""
                           )
    return argparser


if __name__ == '__main__':
    parsed_args = vars(_argparser().parse_args())
    envdir = parsed_args['envdir']
    for subdir in os.listdir(envdir):
        eg = EnvironmentGenerator(os.path.join(envdir, subdir))
        eg.render()
