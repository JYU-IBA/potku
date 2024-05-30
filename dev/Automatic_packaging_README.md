# Automatic packaging of Potku

## The workflow files

Currently automatic packaging doesn't run tests. The process is managed by ``version_bump.yml`` workflow file, which uses `compile_c_apps.yml` and `package_potku.yml` as subprocesses. ``version_bump.yml``
first checks that the creator of the bumping pull request has proper permissions and that only ``version.txt`` is changed. After this the `version.txt` file's contents are verified. If both
of these check pass, then the pull request is automatically approved, merged to master and tagged with the new version number.

Following the new tag, the C applications are compiled using the ``build.bat`` and `build.sh` scripts for their respective operating systems. The `compile_c_apps.yml` workflow first checks
that if any previously created artifacts for the C applications exist in order to speed up packaging. If previous artifacts are found, the workflow then checks if any changes in the
``external`` directory are made. If changes are made since the previous tag then the C apps are compiled again. GitHub retains uploaded artifacts for 90 days at most, so the compilation process
must be rerun at the latest when the artifacts expire.

The `package_potku.yml` workflow finishes the packaging process by first creating a new release for the new tag. After this C applications are downloaded and external files are fetched by
running the `external_file_manager.py` script with 'fetch' as commandline argument. If any of the files in the `external_manifest.txt` fails to download or the SHA256 hash is mismatched against
the `external_manifest.txt`, the whole packaging process is set to fail.

## External file manager

The `external_file_manager.py` script together with `external_manifest.txt` is used to manage the external files Potku and JIBAL use. The script can be run without arguments on a terminal
to access a simple interface, in which the user can enter numbers to run specific actions. By using a commandline argument 'fetch' the user can skip the interface to run the force download
command of the script.

The actions implemented in the script are the following:
1. Fetch absent and out of sync files. The manager downloads only the external files, whose SHA256 hash doesn't match with the external manifest and files that exist in the manifest, but not locally.
2. Force download all files. Downloads all files in the external manifest and overwrites any existing local files.
3. Update manifest with local out of sync files. This action adds any local files, that don't exist in the manifest, into the manifest. Link keys need to be entered manually.
4. Updates the manifest with all local files. This replaces the SHA256 hashes of all the files in the external manifest with your local files' hashes and adds files that exist only locally.
5. Create an entirely new manifest file. This action discards the previous external manifest completely and creates a new on based on the local files.
6. Cancel the process.

The manifest file contains JSON dictionary entries for each file, the keys with file_path: as the relative path to Potku root, date: the date at which the external file was hashed and
entered into the manifest, hash: the sha256 hash of the file, and finally link: the file ID portion of a permanent URL. Currently, Dropbox is used as cloud storage, but basically any service
can be used in which a permanent link with no redirects can be created for a file. The manager script uses  the file_path to identify file names and locations, sha256 for identifying file
version and the link for downloading the files. Date is used only for developers to check manually if needed.

Care should be taken with the link key of the dictionaries! The script independently copies over the links of existing files when updating, but when a link changes or an entirely new file is
added, the link entry for that particular file has to be edited in manually. This script is used together with the automatic packaging and if any downloads fail, the whole packaging is set
to fail to avoid releasing broken versions.

## Future development of the automatic packaging.

As the automatic packaging works on the master branch specifically, it is best to develop any new changes in a separate fork of Potku in order to have a proper environment to test the GitHub
actions workflows. This can be easily done on GitHub and following this the developer should set similar settings as on the actual Potku repository. Mainly in the actions tab 
you should allow all actions and reusable workflows, give workflows read and write permissions and allow GitHub Actions to create and approve pull requests. Finally, in the branches section
the developer should set a protection rule for the master branch and require pull requests before merging, with one approval. This way the main Potku repository's behaviour is replicated and
the functionality of the workflows can be properly tested.

The [bump_version.py](bump_version.py) script can be given a parameter '`--remote` to specify another remote besides `origin` (default). See `git remote add` and `git remote -v` for inspiration. This way 
you can test the packaging in your own repository without having two copies of Potku git.

Use `gh repo set-default` to set the default repository for the GitHub CLI client.