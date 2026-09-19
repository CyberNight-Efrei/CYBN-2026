The provided files are :
	- an ecrypted secret
	- a tool to encrypt/decrypt

As an OSINT challenge, the goal is to retrieve the Key used, through public information.

We could use the name and comments of the script to understand the name of the projet : `TOTALLY INDEPENDANT AES ENCRYPT / DECRYPT TOOL`, or shorten as `TIAEDT`

Description tells he shared his tools online, let's look up on github.

Only one project match the shorten name : [https://github.com/johnneuill/TIAEDT](https://github.com/johnneuill/TIAEDT)
Looking backward in the previous commits, we can find hardcoded Key and IV
using this version of the script, or just using these keys of the version priovided allows us to decrypt the secret : `CYBN{l0ok1Ng_oN_1nT3rNEt_15_Ez_R1gH7?}`