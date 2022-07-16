%global _debugsource_template %{nil}

Name: openlitespeed
Version: 1.7.16
Release: 1
Source0: https://openlitespeed.org/packages/openlitespeed-%{version}.src.tgz
Source1: third-party-20220716.tar.xz
# [Not used, generates Source1]
Source101: package-thirdparty.sh
Patch0: openlitespeed-1.7.16-openmandriva.patch
Patch1: openlitespeed-1.7.16-yajl-sources-have-moved.patch
Patch2: openlitespeed-1.7.16-fix-build-with-preexisting-third-party.patch
Patch3: openlitespeed-1.7.16-system-libs.patch
Patch4: openlitespeed-1.7.16-no-prebuilt-php.patch
Summary: High performance, lightweight web server
URL: https://openlitespeed.org/
License: GPLv3
Group: Servers
BuildRequires: cmake
BuildRequires: make
# Only after applying the system libs patch
BuildRequires: pkgconfig(zlib)
BuildRequires: pkgconfig(libbrotlidec)
BuildRequires: pkgconfig(libbrotlienc)
BuildRequires: pkgconfig(expat)
BuildRequires: pkgconfig(libxml-2.0)
BuildRequires: pkgconfig(libpcre)
BuildRequires: pkgconfig(yajl)
BuildRequires: pkgconfig(luajit)
BuildRequires: pkgconfig(libzmq)
BuildRequires: pkgconfig(libmaxminddb)
BuildRequires: pkgconfig(lmdb)
BuildRequires: openldap-devel
# Just to make install.sh happy
BuildRequires: php-openlitespeed
# Just so the internal boringssl fork will build
BuildRequires: golang

%description
High performance, lightweight web server

%prep
# Not using autosetup so we can apply patches
# after unpacking additional sources
%autosetup -p1 -a1
rm -rf ../third-party
mv third-party ..
# These locations are _supposed_ to be configurable, but they're
# actually hardcoded in a number of places. Let's replace them
# globally with sed so we don't miss any new hardcodes on updates...
find . -type f |xargs sed -i -e 's,/tmp/lshttpd,/run/lshttpd,g;s,/usr/local/lsws,/opt/openlitespeed,g'

%build
./build.sh
[ -e dist/bin/openlitespeed ] || exit 1

%install
sed -i "s#SERVERROOT=/opt/openlitespeed#SERVERROOT=%{buildroot}/opt/openlitespeed#" ols.conf
./install.sh

# Fix symlink into buildroot
rm "%{buildroot}"/opt/openlitespeed/fcgi-bin/lsphp
ln -s lsphp5 "%{buildroot}"/opt/openlitespeed/fcgi-bin/lsphp

# Fix some permissions.
find "%{buildroot}"/opt/openlitespeed/conf -type d |xargs chmod 0750
find "%{buildroot}"/opt/openlitespeed/conf -type f |xargs chmod 0640
find "%{buildroot}"/opt/openlitespeed/tmp -type d |xargs chmod 0750
find "%{buildroot}"/opt/openlitespeed/admin/conf -type d |xargs chmod 0700
find "%{buildroot}"/opt/openlitespeed/admin/conf -type f |xargs chmod 0600
find "%{buildroot}"/opt/openlitespeed/admin/tmp -type d |xargs chmod 0750

# Remove stuff specific to other distros
rm -f "%{buildroot}"/opt/openlitespeed/admin/misc/lsws.rc.gentoo \
      "%{buildroot}"/opt/openlitespeed/admin/misc/lsws.rc \
      "%{buildroot}"/opt/openlitespeed/admin/misc/rc-inst.sh \
      "%{buildroot}"/opt/openlitespeed/admin/misc/rc-uninst.sh \
      "%{buildroot}"/opt/openlitespeed/admin/misc/uninstall.sh

# Remove build root from installed files
sed -i "s#%{buildroot}##g" %{buildroot}/opt/openlitespeed/admin/misc/*

# Move some stuff where it can be seen
mkdir -p %{buildroot}%{_unitdir}
mv %{buildroot}/opt/openlitespeed/admin/misc/lshttpd.service %{buildroot}%{_unitdir}/

%files
/opt/openlitespeed
%{_unitdir}/lshttpd.service
