{{- define "timeio.publicUrl" -}}
{{- default .Values.global.ingress.url .Values.global.publicUrl -}}
{{- end -}}

{{- define "timeio.publicHost" -}}
{{- $publicUrl := include "timeio.publicUrl" . -}}
{{- default (urlParse $publicUrl).host .Values.global.publicHost -}}
{{- end -}}

{{- define "timeio.oidcIssuer" -}}
{{- printf "%s/keycloak/realms/timeio" (include "timeio.publicUrl" .) -}}
{{- end -}}

{{- define "timeio.oidcConfUrl" -}}
{{- printf "%s/.well-known/openid-configuration" (include "timeio.oidcIssuer" .) -}}
{{- end -}}

{{- define "timeio.oidcAuthUrl" -}}
{{- printf "%s/protocol/openid-connect/auth" (include "timeio.oidcIssuer" .) -}}
{{- end -}}

{{- define "timeio.oidcTokenUrl" -}}
{{- printf "%s/protocol/openid-connect/token" (include "timeio.oidcIssuer" .) -}}
{{- end -}}

{{- define "timeio.oidcUserinfoUrl" -}}
{{- printf "%s/protocol/openid-connect/userinfo" (include "timeio.oidcIssuer" .) -}}
{{- end -}}
