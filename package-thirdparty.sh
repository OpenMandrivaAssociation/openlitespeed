#!/bin/sh
rm -rf third-party
git clone --recursive --depth 1 https://github.com/litespeedtech/third-party.git
D="$(date +%Y%m%d)"
cd third-party/src
git clone --depth 1 -b v3.0.5 https://github.com/SpiderLabs/ModSecurity.git
git clone --depth 1 https://github.com/curl/curl.git
git clone --depth 1 https://github.com/litespeedtech/libbcrypt.git
cd ../..
# Can't use git archive or git-archive-all.sh or the likes because
# the insane build process actually tries to switch branches!
tar cf third-party-$D.tar third-party
xz -9ef third-party-$D.tar
