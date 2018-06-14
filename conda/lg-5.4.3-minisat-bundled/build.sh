#tar -xzf link-grammar-5.4.4.tar.gz
#cd link-grammar-5.4.3
./configure --prefix=$PREFIX --enable-sat-solver=bundled --enable-python-bindings=3
make
make check
make install
ldconfig -r $PREFIX -N
make installcheck
