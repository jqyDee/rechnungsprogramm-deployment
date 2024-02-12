# Rechnungsprogramm DEPLOYMENT
Deployment pipeline for rechnungsprogramm

## Requirements

Python3 and gh is needed to run script (to install gh through brew run ```brew install gh```)

## Command

```
python <kind> <path-to-deploy.py> <path-to-src-file> <dest-path-in-sftp-server> <version-number> <v>
```

```kind``` can be either ```m``` or ```u```

```v``` makes the output verbose and is optional

### Command help Rechnungsprogramm (user specific)
```python /Users/mfischbach/Developer/python/rechnungsprogramm-deployment/deploy.py m /Users/mfischbach/Developer/python/rechnungsprogramm/main.py / 3.7.13```

## Footer

Copyright: 2023 Matti Fischbach

Developer: Matti Fischbach 
