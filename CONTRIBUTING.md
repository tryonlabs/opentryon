## How to contribute to tryondiffusion

### 1. Open an issue
We recommend opening an issue (if one doesn't already exist) and discussing your intended changes before making any changes. 
We'll be able to provide you feedback and confirm the planned modifications this way.

### 2. Make changes in the code
Start with forking the repository, set up the environment, install the dependencies, and make changes in the code appropriately. 

### 3. Create pull request
Create a pull request to the main branch from your fork's branch.

### 4. Merging pull request
Once the pull request is created, we will review the code changes and merge the pull request as soon as possible.  


### Writing documentation

If you are interested in writing the documentation, you can add it to README.md and create a pull request. 
For now, we are maintaining our documentation in a single file and we will add more files as it grows.

### Adding a new model/adapter

If you're integrating a new cloud API or open-weight/local model, follow the
step-by-step checklist at
[docs/docs/advanced/new-model-checklist.md](docs/docs/advanced/new-model-checklist.md)
(covers where the adapter code goes, dependency management, wiring it into
the `opentryon` CLI, and which docs to update).
