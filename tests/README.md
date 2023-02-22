# Tests

## Basic Overview

clpipe uses pytest as its testing framework.

All test modules belong in the `tests` folder. Each test module should use the following default pytest naming pattern:
`test_<module>`, where `<module>` is the name of the module being tested.

All test functions should use the following default pytest naming pattern:
`test_<function>_<case>`, where `<function>` is function being tested and
`<case>` is the unique case being tested.

clpipe leverages pytest's [fixture](https://docs.pytest.org/en/6.2.x/fixture.html)
feature extensively to provide its test cases with
preconfigured objects for testing. **Any arguments passed into pytests tests are
fixtures**. These fixtures are defined in `tests/conftest.py`.

clpipe's tests often leverage temporary file storage. To control where this
this location is by default, you can use the pytest flag `--basetemp`. 
clpipe's `.gitignore` includes `tests/temp` by default for this purpose. You can point
pytest to this folder like this: `--basetemp tests/temp`, where `temp` is a 
sub-folder manually created to house temporary test files.

Many clpipe tests are not fully transient, and instead save their outputs to allow
for inspection. These output files are saved to `tests/artifacts`, 
which is ignored by git by default.