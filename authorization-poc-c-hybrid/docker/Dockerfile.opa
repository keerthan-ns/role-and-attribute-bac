FROM openpolicyagent/opa:1.18.2
COPY opa/policies /policies
EXPOSE 8181
ENTRYPOINT ["opa"]
CMD ["run","--server","--addr=0.0.0.0:8181","--log-level=error","/policies"]
