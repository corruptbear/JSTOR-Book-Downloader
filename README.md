# README

## Prerequisite

### Access to JSTOR 
An IP address that has access to the JSTOR is required.

### Dependency
```
python3 -m pip install -r requirements.txt
```

## Usage
1. Modify the book url and the parent directory
2. Run the script.

## Notes

- JSTOR is very aggressive in preventing any form of batch download. 
- You might have to redo the captcha during the chapter download process. If the captcha is not finished with in ``time_for_recaptcha``,  the download process will fail, you will have to restart the script.