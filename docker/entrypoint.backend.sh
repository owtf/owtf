#!/usr/bin/env bash

set -euo pipefail

cert_dir="${OWTF_CERT_DIR:-${HOME}/.owtf/proxy/certs}"
ca_cert="${cert_dir}/ca.crt"
ca_key="${cert_dir}/ca.key"
ca_pass_file="${cert_dir}/ca_pass.txt"

cleanup() {
    if [[ -n "${tmp_dir:-}" ]]; then
        rm -f -- "${tmp_dir}/ca.crt" "${tmp_dir}/ca.key" "${tmp_dir}/ca_pass.txt"
        rmdir "${tmp_dir}" 2>/dev/null || true
    fi
}

if [[ ! -s "${ca_cert}" || ! -s "${ca_key}" || ! -s "${ca_pass_file}" ]]; then
    echo "Bootstrapping the OWTF proxy certificate authority in ${cert_dir}"
    umask 077
    mkdir -p "${cert_dir}"

    tmp_dir="$(mktemp -d "${cert_dir}/.bootstrap.XXXXXX")"
    trap cleanup EXIT

    openssl rand -hex 32 > "${tmp_dir}/ca_pass.txt"
    openssl genrsa \
        -aes256 \
        -passout "file:${tmp_dir}/ca_pass.txt" \
        -out "${tmp_dir}/ca.key" \
        4096
    openssl req \
        -new \
        -x509 \
        -days 3650 \
        -subj "/C=US/ST=Pwnland/L=OWASP/O=OWTF/CN=MiTMProxy" \
        -passin "file:${tmp_dir}/ca_pass.txt" \
        -key "${tmp_dir}/ca.key" \
        -out "${tmp_dir}/ca.crt"

    mv -f "${tmp_dir}/ca.crt" "${ca_cert}"
    mv -f "${tmp_dir}/ca.key" "${ca_key}"
    mv -f "${tmp_dir}/ca_pass.txt" "${ca_pass_file}"
    rmdir "${tmp_dir}"
    tmp_dir=""
    trap - EXIT
fi

exec "$@"
