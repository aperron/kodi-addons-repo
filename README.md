

# install this repo

* download build/repository.aperron.zip
* in kodi, install addon from zip
* now, you can browse this repo from kodi

# create my own repo

* fork this github repo

* edit file : `github_repos.csv`

* if necessary, install python and prepare pipenv

    ```sh
    python -m pip install pip --upgrade --user
    python -m pip install pipenv --user
    # add Python Scripts fodler in your path $USER_HOME\AppData\Roaming\Python\Python37\Scripts, if doesn't
    pipenv install
    ```

* generate content of `build` folder

    ```sh
    pipenv run .\addons_xml_generator.py $NAME_OF_FORKED_REPO
    # example: pipenv run .\addons_xml_generator.py aperron/aperron-kodi-addons-repo
    ```

* git push