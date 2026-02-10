#!/bin/sh

search_dir="/usr/share/nginx/html/"

environmentPlaceholders="
ENV_API_BASE_URL_PLACEHOLDER
ENV_OIDC_IDP_URL_PLACEHOLDER
ENV_OIDC_CLIENT_ID_PLACEHOLDER
ENV_OIDC_REDIRECT_URI_PLACEHOLDER
ENV_OIDC_SCOPE_PLACEHOLDER
ENV_OIDC_POST_LOGOUT_REDIRECT_URI_PLACEHOLDER
ENV_BASE_URL_PLACEHOLDER
"

replaceValue()
{
  passedPlaceholder=$1
  value=$(printenv $passedPlaceholder)

  # $@ contains all arguments passed to a function
  # shift removes the first argument passed to the function
  # the remaining arguments are the paths to the files
  shift

  passedFiles=$@

  echo "placeholder: $passedPlaceholder | value: $value"
  sed -i "s|\b$passedPlaceholder\b|${value:-}|g" $passedFiles
}

findFilesByExtensionAndReplacePlaceholders()
{
  fileExtension=$1
  files=$(find "$search_dir" -type f -name "$fileExtension")

  if [ -n "$files" ]; then
    echo "Replacing files with extention: $fileExtension"
    for placeholder in $environmentPlaceholders; do
     replaceValue $placeholder $files
    done
  else
    echo "No files found with extension: $fileExtension"
  fi
}

removeEmptyScriptTags()
{
    # this function is needed to replace the empty script tag of the matomo module in the index.html if no matomo url was passed
    fileExtension=$1
    files=$(find "$search_dir" -type f -name "$fileExtension")

    if [ -n "$files" ]; then
      echo "Replacing empty script tags"
      sed -i 's|<script[^>]*src=""[^>]*></script>||g' $files
    else
      echo "No files found with extension: $fileExtension to replace empty script tags"
    fi
}

findFilesByExtensionAndReplacePlaceholders "*.js"
findFilesByExtensionAndReplacePlaceholders "*.html"
findFilesByExtensionAndReplacePlaceholders "*.json"
findFilesByExtensionAndReplacePlaceholders "*.css"
removeEmptyScriptTags "*.html"

exec "$@"
