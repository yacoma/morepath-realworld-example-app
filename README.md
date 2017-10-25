### ![Morepath RealWorld Example App](logo.png)

> ### Morepath codebase containing real world examples (CRUD, auth, advanced patterns, etc) that adheres to the [RealWorld](https://github.com/gothinkster/realworld) spec and API.


### [Demo](http://conduit.yacoma.it/api/)


This codebase was created to demonstrate a fully fledged fullstack application built with
[**Morepath**](http://morepath.readthedocs.io), using [**Pony**](https://ponyorm.com/)
object-relational mapper, including CRUD operations, authentication, routing, pagination,
and more.

We've gone to great lengths to adhere to the **Morepath** community
[styleguides](http://morepath.readthedocs.io/en/latest/advanced-topics.html)
& best practices.

For more information on how to this works with other frontends/backends, head over to the
[RealWorld](https://github.com/gothinkster/realworld) repo.

A demo api server is running at http://conduit.yacoma.it/api/.


This repo is functionality complete — PRs and issues welcome!

<!-- TOC depthFrom:1 depthTo:2 withLinks:1 updateOnSave:1 orderedList:0 -->

- [Getting started](#getting-started)
- [Code Overview](#code-overview)
	- [Dependencies](#dependencies)
	- [Application Structure](#application-structure)
	- [Error Handling](#error-handling)
	- [Authentication](#authentication)
- [Testing](#testing)

<!-- /TOC -->

# Getting started

Clone this repo and adjust the settings in the settings folder.
Remember to change the master_secret.

From inside the project directory create a clean Python environment with
[virtualenv](https://virtualenv.pypa.io/en/latest) and activate it:

```sh
$ virtualenv -p python3 env
$ source env/bin/activate
```

After this you can install the package including dependencies using:

```sh
(env) $ pip install -Ue .
```

Once that is done you can start the server:

```sh
(env) $ gunicorn conduit.run
```

You can go to <http://localhost:8000> to see the UI.

You can also start the server on another host/port:

```sh
(env) $ gunicorn --bind=example.com:3000 conduit.run
```

# Code Overview

## Dependencies

- Programming language: [Python 3](https://www.python.org)
- Web framework: [Morepath](http://morepath.readthedocs.io)
- Object-Relational Mapper: [PonyORM](https://github.com/morepath/more.pony)
- Authentication: [JSON Web Token (JWT)](https://github.com/morepath/more.jwtauth)
- Validation: [Cerberus](https://github.com/morepath/more.cerberus)
- Creating slugs from article titles: [awesome-slugify](https://github.com/dimka665/awesome-slugify)
- Password hashing: [Argon2](https://argon2-cffi.readthedocs.io)
- WSGI HTTP Server: [gunicorn](http://gunicorn.org)

## Application Structure

The core application under the `conduit` folder contains:

- `run.py` - The entry point to our application. It sets up the database
  and provides a WSGI factory which can be used by a WSGI HTTP Server like
  gunicorn to run the application.
- `app.py` - Sets up the core App and merges the AuthApp, the BlogApp and the
  PonyApp from more.pony in by subclassing from them. It also creates a
  ProductionApp and a TestApp, which are used instead depending on the
  `RUN_ENV` environment variable.
- `permissions.py` - Sets up the permissions and permission rules used to
  protect the views.
- `database.py` - Just creates an instance of the PonyORM `Database`.
- `error_view` - Defines the handling of the Cerberus `ValidationError`.
  For details see below.
- `auth/` - Folder contains the AuthApp.
- `blog/` - Folder contains the BlogApp.
- `settings/`- Folder contains the default settings and the settings
  for production and testing in YAML format.
- `test/` - Folder contains the unit tests.

The subapplication folders `auth/` and `blog/` contain:

- `app.py` - Defines the App.
- `model.py` - Creates the models extended from PonyORM's `db.Entity`.
- `collection.py`- Sets up the collection models.
- `path.py` - Defines the paths depending on the model.
- `view.py` - Creates the views depending on the model.
- `schema.yml` - Contains the schemas used by Cerberus in YAML format.
- `validator.py` - Contains custom validators used by Cerberus (only in `auth`).

## Error Handling

For validating the incoming JSON data on requests we use [Cerberus](http://python-cerberus.org).
The Cerberus schemas are defined in `schema.yml` inside the app folders (`auth/` and `blog/`).
You can also add custom validators, e.g. the `EmailValidator` defined in `auth/validator.py`.

Cerberus returns an `ValidationError`. How to handle the response including returning a 422 status code
and formatting the view is defined in `error_view.py`.

## Authentication

We use the
[Morepath identity policy](http://morepath.readthedocs.io/en/latest/security.html#identity)
provided by [more.jwtauth](https://github.com/morepath/more.jwtauth)
which allows authentication of request through the
[JWT token](http://tools.ietf.org/html/draft-ietf-oauth-json-web-token)
in the `Authorization` header.

# Testing

For installing the test suite and running the tests use:

```sh
(env) $ pip install -Ur requirements/develop.txt
(env) $ py.test
```

To check for test coverage:

```sh
(env) $ py.test --cov
```
The example App has 100% test coverage.

To check if your code is conform with PEP8:

```sh
(env) $ flake8 conduit setup.py
```

You can also run [tox](https://tox.readthedocs.io) locally if you have
installed Python 3.5 or/and Python 3.6:

```sh
(env) $ tox
```
