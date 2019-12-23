# What is going on here ?

This is to solve a problem where it is required to dynamically vary/repeat the number of generated manifests for each 
of the otherwise quite similar dev, qa, staging, prod environments.
  
An environment is usually a set of workloads, e.g microservices, e.g antivirus, ocr and other components that are
 able to scale horizontally and service the complete environment.
But what if we for a given environment want to also run a n-times repeated set of "customer installation" sets as well. 

As an example, we might need to run N instances of a legacy application server (HelmRelease), so we want to define this 
helmrelease manifest just once, and then specify only the small configuration differences for each of needed instances.  

This turns out to be an uneasy scenario to solve with Kustomize, because kustomizations is based on
overlays that targets base manifests using specific (kind,namespace,name) coordinates, and for defining
our N sets of "customer installations" we must vary the name part of the coordinates for each.


# Managing a gitrepo for fluxd

The repo structure is for the initial empty state

```
└── releases
    |—— .flux.yaml 
└── environments
└── basetemplates
```

The releases folder is meant to be configured as the fluxcd --git-path=releases argument 
along with --manifest-generation=true

The environments directory is to be populated with subdirectories defining an instance of our 
workloads. Each subdirectory is to contain an editable copy of the root templates folder,
and by editing these templates it will directly affect everything that is generator
based on these templates.  

The basetemplates folder is for base templates, editing these templates will only affect new
instances, as nothing is directly generated from the base templates

## Populating the basetemplates

The basetemplates are directories with sets of template files, e.g kubernetes yaml manifest files
meant for jinja2 template processing

e.g.
```
└── basetemplates
    └── SET1
        |── template1.yaml
        |── template2.yaml
    └── SET2
        |── template1.yaml
        |── template2.yaml
```

## Create a new workload configuration in the environments folder

An environment instance is expressed as subfolder in the environements folder, containing

1. A snapshot copy of the basetemplates. E.g `cp -r basetemplates environments/NAME`
2. folder `generatorconfigs` with the `.yaml` files with `generatorconfig` manifests  

```
└── environments
    └── NAME
        └── templates
            └── SET1
                |── template1.yaml
                |── template2.yaml
            └── SET2
                |── template1.yaml
                |── template2.yaml
        └── generatorconfigs
            |── SET1-a-generatorconfig.yaml
            |── SET2-b-generatorconfig.yaml
            |── SET2-c-generatorconfig.yaml
            |── SET2-d-generatorconfig.yaml
```
                
# The `generatorconfig` format

The format is meant to be basically just properties, meaning pure configuration without much structure structure.

```
generatorconfigversion: 1
templateset: SET2
id: set2-a
import_substitution_parameters:
  - set1
substitution_parameters:
  NAME1: VALUE
  NAME2: VALUE
overrides:
  - manifest:
      kind: MFKIND
      namespace: MFNAMESPACE
      name: MFNAME 
    values:
      PATH: OVERRIDE
```

There are 2 mandatory parts:
* generatorconfigversion : must be 1
* templateset : pointer to template set directory for the environment, e.g SET2

The rest is optional:
* id: is optional, only useful if other generatorconfig needs to reference this config
* import_substitution_parameters: List of generatorconfig ids to import substitution parameters from. 
Each of the imported parameters can be overridden
* substitution_parameters: is the parameters for jinja2 templating of the templates
* overrides: Use it to override anything in the generated manifests. The section is a list with:
   * manifest: Optional if there is just 1 manifest in the template SET, otherwise the manifest (kind,namespace,name) coordinates
   * values: yaml to override anything in the jinja2 generated manifests


 
