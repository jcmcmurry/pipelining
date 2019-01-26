# ************************************************************************
#
#            TriBITS: Tribal Build, Integrate, and Test System
#                    Copyright 2013 Sandia Corporation
#
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the Corporation nor the names of the
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY SANDIA CORPORATION "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SANDIA CORPORATION OR THE
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ************************************************************************

MACRO(GLOBAL_SET VARNAME)
  SET(${VARNAME} ${ARGN} CACHE INTERNAL "")
ENDMACRO()

MACRO(TRIBITS_ADD_OPTION_AND_DEFINE  USER_OPTION_NAME  MACRO_DEFINE_NAME
  DOCSTRING  DEFAULT_VALUE
  )
  #MESSAGE("TRIBITS_ADD_OPTION_AND_DEFINE: '${USER_OPTION_NAME}' '${MACRO_DEFINE_NAME}' '${DEFAULT_VALUE}'")
  SET( ${USER_OPTION_NAME} "${DEFAULT_VALUE}" CACHE BOOL "${DOCSTRING}" )
  IF(NOT ${MACRO_DEFINE_NAME} STREQUAL "")
    IF(${USER_OPTION_NAME})
      GLOBAL_SET(${MACRO_DEFINE_NAME} ON)
    ELSE()
      GLOBAL_SET(${MACRO_DEFINE_NAME} OFF)
    ENDIF()
  ENDIF()
ENDMACRO()

macro(append_set varname)
  list(APPEND ${varname} ${ARGN})
endmacro(append_set)

FUNCTION(FORTRAN_MANGLING)

  IF(NOT DEFINED FC_FN_CASE)

    IF (${PROJECT_NAME}_VERBOSE_CONFIGURE)
      MESSAGE("FORTRAN_MANGLING: Testing name Mangling Schemes!\n")
    ENDIF()

    FIND_FILE(_fcmakelists fmangle/ ${CMAKE_MODULE_PATH})
    IF (NOT _fcmakelists)
      MESSAGE(STATUS "Error, the directory fmangle could not be found so we can not determine Fortran name mangling!")
      RETURN()
    ENDIF()

    SET(_fcmangledir ${PROJECT_BINARY_DIR}/CMakeFiles/CMakeTmp/fmangle)
    FILE(MAKE_DIRECTORY ${_fcmangledir})

    FOREACH(cdef LOWER UPPER)

      FOREACH(udef UNDER NO_UNDER SECOND_UNDER)

        IF (${PROJECT_NAME}_VERBOSE_CONFIGURE)
          MESSAGE("FORTRAN_MANGLING: Testing ${cdef} ${udef}\n\n")
        ENDIF()

        SET(_fcmangledir_case "${_fcmangledir}/${cdef}/${udef}")
        FILE(MAKE_DIRECTORY "${_fcmangledir}/${cdef}")
        FILE(MAKE_DIRECTORY ${_fcmangledir_case})

        SET(COMMON_DEFS -DFC_FN_${cdef} -DFC_FN_${udef})
        SET(C_FLAGS "${CMAKE_C_FLAGS} ${${PROJECT_NAME}_EXTRA_LINK_FLAGS}")
        SET(F_FLAGS "${CMAKE_Fortran_FLAGS} ${${PROJECT_NAME}_EXTRA_LINK_FLAGS}")
        TRY_COMPILE(_fcmngl ${_fcmangledir_case} ${_fcmakelists} fmangle
          CMAKE_FLAGS
            "-DCMAKE_BUILD_TYPE:STRING=${CMAKE_BUILD_TYPE}"
            "-DCMAKE_C_FLAGS:STRING=${C_FLAGS}"
            "-DCMAKE_C_FLAGS_${CMAKE_BUILD_TYPE}:STRING=${CMAKE_C_FLAGS_${CMAKE_BUILD_TYPE}}"
            "-DCMAKE_Fortran_FLAGS:STRING=${F_FLAGS}"
            "-DCMAKE_Fortran_FLAGS_${CMAKE_BUILD_TYPE}:STRING=${CMAKE_Fortran_FLAGS_${CMAKE_BUILD_TYPE}}"
            "-DCOMMON_DEFS=${COMMON_DEFS}"
          OUTPUT_VARIABLE _fcmngl_output
          )
        IF (${PROJECT_NAME}_VERBOSE_CONFIGURE)
          MESSAGE("${_fcmngl_output}\n\n")
        ENDIF()

        IF(_fcmngl)
          IF (${PROJECT_NAME}_VERBOSE_CONFIGURE)
            MESSAGE("FORTRAN_MANGLING: Bingo!  ${cdef} ${udef} is the correct fortran name mangling!\n")
          ENDIF()
          GLOBAL_SET(FC_FN_CASE ${cdef})
          GLOBAL_SET(FC_FN_UNDERSCORE ${udef})
          BREAK()
        ENDIF()

      ENDFOREACH()

      IF(_fcmngl)
        BREAK()
      ENDIF()

    ENDFOREACH()

    IF(_fcmngl)
      MESSAGE(STATUS "Fortran name mangling: ${FC_FN_CASE} ${FC_FN_UNDERSCORE}")
    ELSE()
      MESSAGE(STATUS "Warning, cannot automatically determine Fortran mangling.")
    ENDIF()

  ENDIF()

  IF (FC_FN_CASE STREQUAL LOWER)
    SET(FC_NAME_NAME name)
  ELSEIF (FC_FN_CASE STREQUAL UPPER)
    SET(FC_NAME_NAME NAME)
  ENDIF()

  IF (FC_FN_UNDERSCORE)
    IF(FC_FN_UNDERSCORE STREQUAL "UNDER")
      SET(FC_FUNC_DEFAULT "(name,NAME) ${FC_NAME_NAME} ## _" CACHE INTERNAL "")
      SET(FC_FUNC__DEFAULT "(name,NAME) ${FC_NAME_NAME} ## _" CACHE INTERNAL "")
    ELSEIF(FC_FN_UNDERSCORE STREQUAL "SECOND_UNDER")
      SET(FC_FUNC_DEFAULT "(name,NAME) ${FC_NAME_NAME} ## _" CACHE INTERNAL "")
      SET(FC_FUNC__DEFAULT "(name,NAME) ${FC_NAME_NAME} ## __" CACHE INTERNAL "")
    ELSE()
      SET(FC_FUNC_DEFAULT "(name,NAME) ${FC_NAME_NAME}" CACHE INTERNAL "")
      SET(FC_FUNC__DEFAULT "(name,NAME) ${FC_NAME_NAME}" CACHE INTERNAL "")
    ENDIF()
  ENDIF()

ENDFUNCTION()


# IF (${PROJECT_NAME}_ENABLE_CXX AND ${PROJECT_NAME}_ENABLE_Fortran)
FORTRAN_MANGLING()
# INCLUDE(FortranCInterface)

# Verify the selected combination of Fortran and C++ compilers.
# IF(NOT ${PROJECT_NAME}_SKIP_FORTRANCINTERFACE_VERIFY_TEST)
  # FortranCInterface_VERIFY(CXX)
# ENDIF()
# ENDIF()

IF (FC_FUNC_DEFAULT)

  SET(F77_FUNC_DEFAULT ${FC_FUNC_DEFAULT})
  SET(F77_FUNC__DEFAULT ${FC_FUNC__DEFAULT})
  # 2008/10/26: rabartl: ToDo: Above, we need to write
  # a different function to find out the right BLAS
  # name mangling automatically.  Given what the above
  # FORTRAN_MANGLING() function does, this should not
  # be too hard.

ELSE()

  IF(CYGWIN)
    SET(F77_FUNC_DEFAULT "(name,NAME) name ## _" )
    SET(F77_FUNC__DEFAULT "(name,NAME) name ## __" )
  ELSEIF(WIN32)
    SET(F77_FUNC_DEFAULT "(name,NAME) name ## _" )
    SET(F77_FUNC__DEFAULT "(name,NAME) NAME")
  ELSEIF(UNIX AND NOT APPLE)
    SET(F77_FUNC_DEFAULT "(name,NAME) name ## _" )
    #SET(F77_FUNC__DEFAULT "(name,NAME) name ## __" )
    SET(F77_FUNC__DEFAULT "(name,NAME) name ## _" )
  ELSEIF(APPLE)
    SET(F77_FUNC_DEFAULT "(name,NAME) name ## _" )
    SET(F77_FUNC__DEFAULT "(name,NAME) name ## __" )
  ELSE()
    MESSAGE(FATAL_ERROR "Error, could not determine fortran name mangling!")
  ENDIF()

ENDIF()

# Set options so that users can change these!

SET(F77_FUNC ${F77_FUNC_DEFAULT} CACHE STRING
  "Name mangling used to call Fortran 77 functions with no underscores in the name")
SET(F77_FUNC_ ${F77_FUNC__DEFAULT} CACHE STRING
  "Name mangling used to call Fortran 77 functions with at least one underscore in the name")

MARK_AS_ADVANCED(F77_FUNC)
MARK_AS_ADVANCED(F77_FUNC_)
