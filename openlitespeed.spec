###############################################################################
# OpenLiteSpeed RPM spec – OpenMandriva style
# Uses system shared libraries and FHS-compliant paths.
###############################################################################

%bcond_without system_libs

Name:           openlitespeed
Version:        1.9.2
Release:        1
Summary:        High-performance, lightweight HTTP server
License:        GPLv3+
Group:          System/Servers
URL:            https://openlitespeed.org
Source0:        https://github.com/litespeedtech/openlitespeed/archive/refs/tags/v%{version}.tar.gz
# See LSQUICCOMMIT / lsquic .gitmodules
Source1:	https://github.com/litespeedtech/lsquic/archive/19547405c24f60c4537478d38f4214e990be1f95.tar.gz
Source2:	https://github.com/litespeedtech/ls-hpack/archive/cf0f70dd10b352194c97448eb5d00b4aa484f531.tar.gz
Source3:	https://github.com/litespeedtech/ls-qpack/archive/91567706c41c0d97ab8dc576873ecd472d7869fa.tar.gz
# lsquic CI pin; stock OpenSSL has no SSL_QUIC_METHOD / EVP_AEAD
Source4:	https://github.com/google/boringssl/archive/refs/tags/0.20250807.0.tar.gz#/boringssl-0.20250807.0.tar.gz

# ---------------------------------------------------------------------------
# System libraries for everything that has a distro equivalent.  HTTP/3 still
# needs a private BoringSSL (Source4) because lsquic's QUIC TLS hooks are not
# implementable with OpenSSL's public API.
# ---------------------------------------------------------------------------
BuildRequires:  cmake
BuildRequires:  ninja
BuildRequires:  perl
BuildRequires:  pkgconfig(zlib)
BuildRequires:  pkgconfig(libpcre2-8)
BuildRequires:  pkgconfig(libcrypt)
BuildRequires:  pkgconfig(expat)
BuildRequires:  pkgconfig(libxml-2.0)
BuildRequires:  pkgconfig(libbrotlienc)
BuildRequires:  pkgconfig(libbrotlidec)
BuildRequires:  pkgconfig(libmaxminddb)
BuildRequires:  udns-devel
BuildRequires:  libcap-devel
BuildRequires:  libaio-devel
BuildRequires:  systemd-rpm-macros
BuildSystem:	cmake
BuildOption:	-DUSE_SYSTEM_LIBS=ON
BuildOption:	-DFHS_LAYOUT=ON
BuildOption:	-DOLS_CONF_DIR=%{_sysconfdir}/%{name}
BuildOption:	-DOLS_LOG_DIR=%{_localstatedir}/log/%{name}
BuildOption:	-DOLS_RUN_DIR=%{_localstatedir}/run/%{name}
BuildOption:	-DOLS_LIB_DIR=%{_libdir}/%{name}
BuildOption:	-DOLS_SHARE_DIR=%{_datadir}/%{name}
BuildOption:	-DOLS_DOC_ROOT=/srv/%{name}
BuildOption:	-DOLS_TMP_DIR=%{_localstatedir}/run/%{name}/tmp
BuildOption:	-DMOD_PAGESPEED=OFF
BuildOption:	-DMOD_SECURITY=OFF
BuildOption:	-DMOD_LUA=OFF

Requires(pre):  shadow
# openssl(1) is invoked by admin/ACME helper scripts
Requires:       openssl

%patchlist
openlitespeed-packaging.patch

%description
OpenLiteSpeed is the Open Source edition of LiteSpeed Web Server Enterprise.
It features HTTP/3 (QUIC), HTTP/2, event-driven architecture, and a
built-in web-based administration interface.

This package is built against system shared libraries (PCRE2, zlib, expat,
brotli, maxminddb, udns, libxcrypt, …) and installs to FHS-compliant
locations.  HTTP/3 uses a privately built BoringSSL, which is the TLS
library lsquic supports.

# ---------------------------------------------------------------------------
%prep
%autosetup -p1 -n %{name}-%{version}
tar xf %{S:1}
rmdir lsquic
mv lsquic-* lsquic
tar xf %{S:4}
cd lsquic/src
rmdir lshpack
tar xf %{S:2}
mv ls-hpack-* lshpack
cd liblsquic
rmdir ls-qpack
tar xf %{S:3}
mv ls-qpack-* ls-qpack

# ---------------------------------------------------------------------------
# Must run before generated %conf: OLS cmake looks for ssl/libssl.a
%conf -p
cmake -S boringssl-0.20250807.0 -B boringssl-build \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DCMAKE_POSITION_INDEPENDENT_CODE=ON \
	-GNinja
cmake --build boringssl-build --target ssl crypto decrepit
mkdir -p ssl
cp -a boringssl-0.20250807.0/include ssl/
cp boringssl-build/libssl.a boringssl-build/libcrypto.a \
	boringssl-build/libdecrepit.a ssl/

# ---------------------------------------------------------------------------
%install -a
# lsquic's own cmake install() dumps a public static lib + cmake package
rm -f %{buildroot}%{_libdir}/liblsquic.a
rm -rf %{buildroot}%{_datadir}/lsquic
# /run is created by tmpfiles.d, not packaged
rm -rf %{buildroot}%{_localstatedir}/run/%{name}

# Generate an actual httpd_config.conf from the template for the package.
# The sed call fills in the FHS paths the same way the upstream install.sh
# would, but targeting the distro layout.
install -d -m 0755 %{buildroot}%{_sysconfdir}/%{name}
install -d -m 0755 %{buildroot}%{_sysconfdir}/%{name}/admin
install -d -m 0755 %{buildroot}%{_sysconfdir}/%{name}/vhosts
install -d -m 0755 %{buildroot}%{_sysconfdir}/%{name}/vhosts/Example
install -d -m 0755 %{buildroot}%{_sysconfdir}/%{name}/templates
install -d -m 0755 %{buildroot}%{_sysconfdir}/%{name}/cert
install -d -m 0750 %{buildroot}%{_localstatedir}/log/%{name}
install -d -m 0750 %{buildroot}%{_localstatedir}/log/%{name}/admin
install -d -m 0755 %{buildroot}/srv/%{name}
install -d -m 0755 %{buildroot}/srv/%{name}/Example
install -d -m 0755 %{buildroot}%{_libdir}/%{name}/modules

sed -e 's|%%USER%%|openlitespeed|g' \
    -e 's|%%GROUP%%|openlitespeed|g' \
    -e 's|%%ADMIN_EMAIL%%|root@localhost|g' \
    -e 's|%%HTTP_PORT%%|8088|g' \
    -e 's|%%DEFAULT_TMP_DIR%%|%{_localstatedir}/run/%{name}/tmp|g' \
    -e 's|%%RUBY_BIN%%||g' \
    -e 's|%%CONF_DIR%%|%{_sysconfdir}/%{name}|g' \
    -e 's|%%LOG_DIR%%|%{_localstatedir}/log/%{name}|g' \
    -e 's|%%DOC_ROOT%%|/srv/%{name}|g' \
    -e 's|%%FCGI_DIR%%|%{_datadir}/%{name}/fcgi-bin|g' \
    dist/conf/httpd_config.conf.in \
    > %{buildroot}%{_sysconfdir}/%{name}/httpd_config.conf

# Install config sub-files that CMake install rules already placed
# (mime.properties, templates, vhost config)
# They are already handled by CMake install(), but double-check presence:
if [ ! -f %{buildroot}%{_sysconfdir}/%{name}/mime.properties ]; then
    install -m 0644 dist/conf/mime.properties %{buildroot}%{_sysconfdir}/%{name}/
fi

# Install example vhost config
install -m 0644 dist/conf/vhosts/Example/vhconf.conf \
    %{buildroot}%{_sysconfdir}/%{name}/vhosts/Example/

# Install template configs
for f in dist/conf/templates/*.conf; do
    install -m 0644 "$f" %{buildroot}%{_sysconfdir}/%{name}/templates/
done

# Example vhost lives in %%{_datadir}; /srv docroot stays empty for the admin.
find %{buildroot}%{_datadir}/%{name} -name '.htaccess' -delete
find %{buildroot}%{_datadir}/%{name} -type f \( -name '*.html' -o -name '*.css' \
	-o -name '*.php' -o -name '*.js' -o -name '*.svg' -o -name '*.png' \) \
	-exec chmod 0644 {} +

# systemd service
install -D -m 0644 /dev/stdin %{buildroot}%{_unitdir}/%{name}.service <<'EOF'
[Unit]
Description=OpenLiteSpeed HTTP Server
After=network-online.target remote-fs.target nss-lookup.target
Wants=network-online.target

[Service]
Type=forking
PIDFile=%{_localstatedir}/run/%{name}/lshttpd.pid
ExecStart=%{_sbindir}/lswsctrl start
ExecReload=%{_sbindir}/lswsctrl restart
ExecStop=%{_sbindir}/lswsctrl delay-stop
KillMode=none
PrivateTmp=false
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
Alias=lsws.service
EOF

# tmpfiles.d for /run
install -D -m 0644 /dev/stdin \
    %{buildroot}%{_tmpfilesdir}/%{name}.conf <<'EOF'
d %{_localstatedir}/run/%{name}     0755 openlitespeed openlitespeed -
d %{_localstatedir}/run/%{name}/tmp 0755 openlitespeed openlitespeed -
EOF

# Symlink litespeed -> openlitespeed for compat
ln -sf openlitespeed %{buildroot}%{_sbindir}/lshttpd

# ---------------------------------------------------------------------------
%pre
getent group openlitespeed >/dev/null || \
    groupadd -r openlitespeed
getent passwd openlitespeed >/dev/null || \
    useradd -r -g openlitespeed -d /srv/%{name} \
        -s /sbin/nologin -c "OpenLiteSpeed HTTP Server" openlitespeed
exit 0

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

# ---------------------------------------------------------------------------
%files
# Binaries
%{_sbindir}/openlitespeed
%{_sbindir}/lshttpd
%{_sbindir}/lswsctrl
%{_sbindir}/ls_shmstat
%{_sbindir}/ls_shmhashstat

# Configuration
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/httpd_config.conf
%config(noreplace) %{_sysconfdir}/%{name}/mime.properties
%dir %{_sysconfdir}/%{name}/admin
%config(noreplace) %{_sysconfdir}/%{name}/admin/php.ini
%dir %{_sysconfdir}/%{name}/cert
%dir %{_sysconfdir}/%{name}/templates
%config(noreplace) %{_sysconfdir}/%{name}/templates/*.conf
%dir %{_sysconfdir}/%{name}/vhosts
%dir %{_sysconfdir}/%{name}/vhosts/Example
%config(noreplace) %{_sysconfdir}/%{name}/vhosts/Example/vhconf.conf
%config(noreplace) %{_sysconfdir}/%{name}/vhosts/Example/htgroup
%config(noreplace) %{_sysconfdir}/%{name}/vhosts/Example/htpasswd

# Modules
%dir %{_libdir}/%{name}
%dir %{_libdir}/%{name}/modules

# Shared data
%{_datadir}/%{name}/

# Logs (runtime / PID dirs come from tmpfiles.d)
%dir %attr(0750,openlitespeed,openlitespeed) %{_localstatedir}/log/%{name}
%dir %attr(0750,openlitespeed,openlitespeed) %{_localstatedir}/log/%{name}/admin

# Document root
%dir /srv/%{name}
%dir /srv/%{name}/Example

# systemd
%{_unitdir}/%{name}.service
%{_tmpfilesdir}/%{name}.conf

# License & docs
%license GPL.txt
%doc README.md
%doc PACKAGING.md
