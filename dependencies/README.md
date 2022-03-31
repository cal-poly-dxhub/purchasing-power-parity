Lambda functions can access dependencies in multiple ways, but two of the
most common are:
	1. Deployment Packages
	2. Lambda Layers.

Deployment packages are great until the package size is greater than 10MB.

Layers are extremely convenient and I suggest using them.

A layer is a zipped archive of libraries, code, etc., that can be accessed
by any lambda function we need. In other words, we can zip up dependencies
and create a layer for that zip file, and any lambda function can access it
once we give access to the layer through CLI or console.

For python, the directory structure of a layer must be python/{folder},
where each folder is a dependency library.

Ideally, we would still create a deployment package but it will only contain
the source files, and layers will take care of the rest. This will allow
for quicker upload time.
