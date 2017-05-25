#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.69])
AC_INIT([simbuto], [0.1.8], [nobodyinperson@gmx.de])

m4_include([m4/ax_python_module.m4])

# check for python3
AC_CHECK_PROG([python3_bin],[python3],[yes],[no])
test "$python3_bin" != "yes" && AC_MSG_ERROR([no python3 installation found])
# check python modules
AX_PYTHON_MODULE(rpy2,fatal,python3)
AX_PYTHON_MODULE(gi,fatal,python3)

# check for R
AC_CHECK_PROG([r_bin],[R],[yes],[no])
test "$r_bin" != "yes" && AC_MSG_ERROR([no R installation found])

AC_CONFIG_FILES([Makefile])
AC_OUTPUT
