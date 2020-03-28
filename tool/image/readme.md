
### tester archux images

#### how to run tests locally

prerequisites:
* ensure `sudo` rights for user account 
* install https://github.com/random-python/nspawn
* to produce base image, invoke `arch/base/build.py`

individual test image:
* navigate to image folder, say `test/cryptsetup`
* to build test image, run `./build.py`
* to update test machine, run `./setup.py`
* to invoke tests in machine, run `./verify.py`

operate currently active machines:
* invoke `machinectl` to see the list
* invoke `machinectl shell test-cryptsetup` to enter container

### qemu tests require

https://www.archlinux.org/packages/?name=qemu
