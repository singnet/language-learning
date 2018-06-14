./configure --prefix=$PREFIX --enable-sat-solver=bundled --enable-python-bindings=3
make
make check
make install
ldconfig -r $PREFIX -N
make installcheck
