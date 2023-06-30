## Development

To hack around, and develop `faasmctl` itself, you just need to activate the
development virtual environment:

```bash
source ./bin/workon.sh
inv -l
```

### Code formatting

The integration tests run a code formatting check. To make sure your code is
well formatted you may run:

```bash
inv foramt-code
```

### Code versioning

`faasmctl` follows [SemVer v2](https://semver.org/). To bump the code version
and tag a new release on Github you may run:

```bash
# Default is patch
inv git.bump [--patch,--minor,--major]
```

Then, tag the code on GitHub:

```bash
inv git.tag
```
