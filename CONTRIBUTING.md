# You can contribute multiple parts of this project:

micrOS framework and DevToolKit main feature areas:
> Use Commit msg labels in `[Component][Area]`

## [micrOS][Core]

```
  micrOS/source/
    all files without LM_ prefix, micrOS framework core resources.
```

> most hardcore and optimized area, covers critical functionalities.


## [micrOS][LoadModule]

```
  micrOS/source/
    all files with LM_ prefix, micrOS application modules (mainly periphery handling)
```


## TESTING: After Core and LM change run micrOS-linter

```
devToolKit.py -lint
or
devToolKit.py --linter
```

-----------------


## [devToolKit][ToolKit]

```
toolkit/
toolkit/lib
  all python files in this folders impacts devToolKit scripts
    SoC deployment, OTA update, socket coomunication, etc...
```

## [devToolKit][dashboard_apps]

```
toolkit/dashboard_apps
  all files here will be shown as dashboard applications, these you can execute on devices.
    socket applications, system_test, neopixel tests, etc...
```


## [devToolKit][Gateway]

```
toolkit/Gateway.py
tookit/*.html
  Gateway REST api implementation.
    micrOS gateway web application - shows all micrOS nodes and expose common interface for all.
```

## TESTING: test impacted areas manually

```
devToolKit.py -h
...
```
