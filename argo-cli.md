## ArgoCD cli 

[Install](https://foxutech.medium.com/argo-cd-cli-installation-and-commands-65ab578ed75) argocd-cli 

Linux:

```
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd
```

Mac:

```
brew install argocd
```

Windows:

Download With PowerShell: Invoke-WebRequest

You can view the latest version of Argo CD at the link above or run the following command to grab the version:

```
$version = (Invoke-RestMethod https://api.github.com/repos/argoproj/argo-cd/releases/latest).tag_name
```

Replace $version in the command below with the version of Argo CD you would like to download:

```
$url = "https://github.com/argoproj/argo-cd/releases/download/" + $version + "/argocd-windows-amd64.exe"
$output = "argocd.exe"
Invoke-WebRequest -Uri $url -OutFile $output
```

> Note: Also please note you will probably need to move the file into your PATH.


ArgoCD cli [guide](https://argo-cd.readthedocs.io/en/stable/user-guide/commands/argocd_login/)

change password [link](https://argo-cd.readthedocs.io/en/stable/getting_started/#4-login-using-the-cli)
show applications 

Log in:

```
argocd login localhost:30080 --username admin --password <Paste here> --insecure
```

```
Usage:
  argocd [flags]
  argocd [command]

Available Commands:
  account     Manage account settings
  admin       Contains a set of commands useful for Argo CD administrators and requires direct Kubernetes access
  app         Manage applications
  appset      Manage ApplicationSets
  cert        Manage repository certificates and SSH known hosts entries
  cluster     Manage cluster credentials
  completion  output shell completion code for the specified shell (bash, zsh or fish)
  context     Switch between contexts
  gpg         Manage GPG keys used for signature verification
  help        Help about any command
  login       Log in to Argo CD
  logout      Log out from Argo CD
  proj        Manage projects
  relogin     Refresh an expired authenticate token
  repo        Manage repository connection parameters
  repocreds   Manage repository connection parameters
  version     Print version information
  ```
List applications:

```
argocd app list
```

Set new admin password:

```
argocd account update-password --account admin --current-password 'admin_password' --new-password 'new_password'
```