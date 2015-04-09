#This script will patch the openssl in kali linux to support sslv2 
#for more info visit 
#http://blog.opensecurityresearch.com/2013/05/fixing-sslv2-support-in-kali-linux.html

apt-get install devscripts quilt
apt-get source openssl
function ssl_patcher()
{
        cd openssl-*;
        quilt pop -a
        sed -i '/ssltest_no_sslv2.patch/d' ./debian/patches/series;
        sed -i 's/no-ssl2//g' ./debian/rules;
        dch –n 'Allow SSLv2';
        dpkg-source --commit;
        debuild -uc -us;
        cd ../;
};
ssl_patcher
sudo dpkg -i ./*ssl*.deb;
