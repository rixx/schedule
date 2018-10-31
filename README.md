# schedule

Scripts to generate & validate [schedule files](https://c3voc.de/wiki/schedule) for events 
which use the [frab conference system][frab-website].


## 34C3

see https://github.com/voc/schedule/blob/34C3/docs/data_flow_34C3_v0.7.pdf to get an overview and talk to @saerdnaer aka Andi if you have questions.

## Dependencies


### Debian and similar
``` bash
sudo apt-get install python python-pip python-lxml libxslt1-dev
pip install -r requirements.txt
```

### macOS
``` bash
brew install python3
STATIC_DEPS=true pip3 install -r requirements.txt
```
or see https://stackoverflow.com/a/26544099/521791 on how to install lxml


[frab-website]: http://frab.github.io/frab/

