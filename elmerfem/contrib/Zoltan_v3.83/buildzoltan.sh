#note - doesn't seem possible to build shared

mkdir -p builddir
cd builddir

../configure \
--prefix=/usr/local/ \
--enable-mpi --with-mpi-compilers --with-gnumake \
--enable-f90interface \
--with-cflags="-fPIC -m64" \
--with-cxxflags="-fPIC -m64" \
--with-ccflags="-fPIC -m64" \
--with-fcflags="-fPIC -m64" \
# --with-scotch \
# --with-scotch-incdir="/Net/local/proj/all/src/Scotch5" \
# --with-scotch-libdir="/Net/local/proj/linux64/lib/Scotch5" \
# --with-parmetis \
# --with-parmetis-incdir="/Net/local/proj/all/src/ParMETIS3" \
# --with-parmetis-libdir="/Net/local/proj/linux64/lib/ParMETIS3"
make everything
sudo make install
