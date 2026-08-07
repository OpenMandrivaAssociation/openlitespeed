###############################################################################
# OpenLiteSpeed RPM spec – OpenMandriva style
# Uses system shared libraries and FHS-compliant paths.
###############################################################################

%bcond_without system_libs

Name:           openlitespeed
Version:        1.9.0.1
Release:        1
Summary:        High-performance, lightweight HTTP server
License:        GPLv3+
Group:          System/Servers
URL:            https://openlitespeed.org
Source0:        https://github.com/litespeedtech/openlitespeed/archive/refs/tags/v%{version}.tar.gz
# See https://github.com/litespeedtech/openlitespeed submodule for the exact version needed
Source1:	https://github.com/litespeedtech/lsquic/archive/3181911301b1aa4f54c1ed690901abc674ee08fb.tar.gz
Source2:	https://github.com/litespeedtech/ls-hpack/archive/8905c024b6d052f083a3d11d0a169b3c2735c8a1.tar.gz
Source3:	https://github.com/litespeedtech/ls-qpack/archive/1a27f87ece031f9e2fbfb29d5b3ef0a72e0a6bbb.tar.gz

# ---------------------------------------------------------------------------
# Build dependencies – every library the upstream bundles is listed here so
# the distro-provided shared version is used instead.
# ---------------------------------------------------------------------------
BuildRequires:  cmake
BuildRequires:  ninja
BuildRequires:  perl
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(zlib)
BuildRequires:  pkgconfig(libpcre)
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
Requires:       openssl
Requires:       pcre
Requires:       expat
Requires:       zlib

%patchlist
openlitespeed-packaging.patch

%description
OpenLiteSpeed is the Open Source edition of LiteSpeed Web Server Enterprise.
It features HTTP/3 (QUIC), HTTP/2, event-driven architecture, and a
built-in web-based administration interface.

This package is built against system shared libraries and installs to
FHS-compliant locations.

# ---------------------------------------------------------------------------
%prep
%autosetup -p1 -a1 -n %{name}-%{version}
rmdir lsquic
mv lsquic-* lsquic
cd lsquic/src
rmdir lshpack
tar xf %{S:2}
mv ls-hpack-* lshpack
cd liblsquic
rmdir ls-qpack
tar xf %{S:3}
mv ls-qpack-* ls-qpack

# ---------------------------------------------------------------------------
%install -a
%cmake_install

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
install -d -m 0755 %{buildroot}%{_localstatedir}/run/%{name}
install -d -m 0755 %{buildroot}%{_localstatedir}/run/%{name}/tmp
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

# Install example document root
cp -a dist/Example/html %{buildroot}/srv/%{name}/Example/ 2>/dev/null || :
cp -a dist/Example/cgi-bin %{buildroot}/srv/%{name}/Example/ 2>/dev/null || :

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
%dir %{_sysconfdir}/%{name}/cert
%dir %{_sysconfdir}/%{name}/templates
%{_sysconfdir}/%{name}/templates/*.conf
%dir %{_sysconfdir}/%{name}/vhosts
%dir %{_sysconfdir}/%{name}/vhosts/Example
%config(noreplace) %{_sysconfdir}/%{name}/vhosts/Example/vhconf.conf

# Modules
%dir %{_libdir}/%{name}
%dir %{_libdir}/%{name}/modules

# Shared data
%{_datadir}/%{name}/

# Logs
%dir %attr(0750,openlitespeed,openlitespeed) %{_localstatedir}/log/%{name}
%dir %attr(0750,openlitespeed,openlitespeed) %{_localstatedir}/log/%{name}/admin

# Runtime
%dir %attr(0755,openlitespeed,openlitespeed) %{_localstatedir}/run/%{name}
%dir %attr(0755,openlitespeed,openlitespeed) %{_localstatedir}/run/%{name}/tmp

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
