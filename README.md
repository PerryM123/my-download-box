# my-download-box

## Required
###  Python Environment

```sh
$ brew install pyenv
$ cd ~/workspace/my-download-box-backend
$ python3 -m venv myenv
$ source ./myenv/bin/activate
(myenv) $ python --version
Python 3.9.13
```

### Checking if specific package is installed

```sh
$ pip show PACKAGE_NAME
```

`WARNING: Package(s) not found: yt_dlp` が出てきたら `pip install PACKAGE_NAME` でパッケージを導入する必要あります。

## How To Run
```sh
$ python --version
-bash: python: command not found
$ python3 -m venv myenv
$ source ./myenv/bin/activate
(myenv) $ python --version
Python 3.9.13
$ pip install -r requirements.txt
$ python socket_server.py
```

## その他

### How to save a list of saved packages
```sh
$ pip freeze > requirements.txt
```