The issue:
when you copy ecrypt_string result, need to copy everything as exactly starting from !vault | to the end of the string.  But the when you copy it to a variable file, make sure there space between : and !vault |
ansible-playbook --private-key ~/.ssh/tao-web-test.pem -i hosts/hosts --ask-vault-pass -vvvv tradesite_dev.yaml