#!/usr/bin/env python
#
# __COPYRIGHT__
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

"""
Real-world test (courtesy Leanid Nazdrynau) of the multi-step
capabilities of the various Java Builders.
"""

import TestSCons

test = TestSCons.TestSCons()

# This test requires javac
ENV = test.java_ENV()
if test.detect_tool('javac', ENV=ENV):
    where_javac = test.detect('JAVAC', 'javac', ENV=ENV)
else:
    where_javac = test.where_is('javac')
if not where_javac:
    test.skip_test("Could not find Java javac, skipping test(s).\n")


test.subdir(['src'],
            ['src', 'HelloApplet'],
            ['src', 'HelloApplet', 'com'],
            ['src', 'javah'],
            ['src', 'jni'],
            ['src', 'server'],
            ['src', 'server', 'JavaSource'],
            ['src', 'server', 'JavaSource', 'com'],
            ['src', 'server', 'JavaSource', 'com', 'gnu'],
            ['src', 'server', 'JavaSource', 'com', 'gnu', 'scons'],
            ['src', 'server', 'JavaSource', 'com', 'gnu', 'scons', 'web'],
            ['src', 'server', 'JavaSource', 'com', 'gnu', 'scons', 'web', 'tools'],
            ['src', 'server', 'WebContent'],
            ['src', 'server', 'WebContent', 'META-INF'],
            ['src', 'server', 'WebContent', 'WEB-INF'],
            ['src', 'server', 'WebContent', 'WEB-INF', 'conf'],
            ['src', 'server', 'WebContent', 'WEB-INF', 'lib'],
            ['src', 'server', 'WebContent', 'theme'])

test.write(['SConstruct'], """\
import os
env=Environment()
Export('env')
env.PrependENVPath('PATH',os.environ.get('PATH',[]))
env['INCPREFIX']='-I'
env.Append(SWIGFLAGS=['-c++','$_CPPINCFLAGS'])

#this is for JNI
#env.Append(CCFLAGS=['/IN:/jdk/v1.3.1/include','/IN:/jdk/v1.3.1/include/win32'])

#this for windows only C++ build
#env.Append(CXXFLAGS='-GX')

env.Append(CPPPATH='.')

env.BuildDir('buildout', 'src', duplicate=0)

#If you do not have swig on your system please remove 'buildout/jni/SConscript' line from next call
env.SConscript(['buildout/server/JavaSource/SConscript',
                'buildout/HelloApplet/SConscript',
        'buildout/jni/SConscript',
                'buildout/javah/SConscript'])
""")

test.write(['src', 'HelloApplet', 'Hello.html'], """\
<HTML>
<HEAD>
<TITLE> Applet Hello </TITLE>
</HEAD>
<BODY>
<CENTER>
<applet name="Hello" archive="HelloApplet.jar" code="com.Hello.Hello.class"
    width="800" height="286" MAYSCRIPT>
</applet>
</CENTER>
</BODY>
</HTML>

""")

test.write(['src', 'HelloApplet', 'SConscript'], """\
import os
Import ("env")
denv=env.Copy()
classes=denv.Java(target='classes',source=['com'])
#set correct path for jar
denv['JARCHDIR']=os.path.join(denv.Dir('.').get_abspath(),'classes')
denv.Jar('HelloApplet',classes)


#To sign applet you have to create keystore before and made a calls like this

#keystore='/path/to/jarsignkey'
#denv['JARSIGNFLAGS']='-keystore '+keystore+' -storepass pass -keypass passkey'
#denv['JARSIGNALIAS']='ALIAS'
#denv['JARCOM']=[denv['JARCOM'],'$JARSIGNCOM']

""")

test.write(['src', 'HelloApplet', 'com', 'Hello.java'], """\
package com.Hello;
import java.awt.*;
import java.applet.*;

public class Hello extends Applet {
    public void paint(Graphics g) {
    g.drawString("Hello from SCons signed applet",250,150);
    }
    }

""")

test.write(['src', 'javah', 'MyID.cc'], """\
#include "MyID.h"
int getMyID()
{
   return 0;
}
""")

test.write(['src', 'javah', 'MyID.java'], """\
import java.util.*;
import java.io.IOException;
import java.lang.reflect.*;

public class MyID
{
    static private long current = System.currentTimeMillis();
    static public String get()
    {
        current++;
        return new Long( current ).toString();
    }
}
""")

test.write(['src', 'javah', 'SConscript'], """\
Import('env')
denv=env.Copy()
denv['JARCHDIR']=denv.Dir('.').get_abspath()
denv.Jar('myid','MyID.java')
denv.JavaH(denv.Dir('.').get_abspath(),'MyID.java')
denv.SharedLibrary('myid','MyID.cc')

""")

test.write(['src', 'jni', 'A.java'], """\
package web.jni;

import web.jni.*;

public class A
{
class C
{
    void echo2( String text )
    {
        System.out.println( text+"aa" );

    }
}
class B
{
    void echo( String text )
    {
        System.out.println( text );
        C c = new C();
        c.echo2("from B callin C");
    }
}
    public void main( String[] x)
    {
        B b = new B();
        b.echo("123");
        C c = new C();
        c.echo2("456");
    }
}
""")

test.write(['src', 'jni', 'JniWrapper.cc'], """\
#include <vector>
#include <iostream>

#include "JniWrapper.h"



JniWrapper::JniWrapper( JNIEnv *pEnv )
    : mpEnv( pEnv )
{
}

JniWrapper::JniWrapper( const JniWrapper& rJniWrapper )
    : mpEnv( rJniWrapper.mpEnv )
{
}

JniWrapper::~JniWrapper()
{

}

JniWrapper& JniWrapper::operator=( const JniWrapper& rJniWrapper )
{
    if ( this != &rJniWrapper )
    {
        mpEnv = rJniWrapper.mpEnv;
    }
    return *this;
}

std::string JniWrapper::unmarshalString( jstring value )
{
    std::string result;
    if( value )
    {
        const char *pStr = mpEnv->GetStringUTFChars( value, 0 );
        result = pStr;
        mpEnv->ReleaseStringUTFChars( value, pStr );
    }
    return result;
}

jobject JniWrapper::marshalDouble( double value )
{
    jclass classObject = mpEnv->FindClass( "java/lang/Double" );
    jmethodID constructorId = mpEnv->GetMethodID( classObject, "<init>", "(D)V" );
    jobject result = mpEnv->NewObject( classObject, constructorId, value );

    return result;
}

jobject JniWrapper::getVectorElement( jobject values, int i )
{
    jclass vectorClass = mpEnv->FindClass( "java/util/Vector" );
    jmethodID methodID = mpEnv->GetMethodID( vectorClass,
                                             "elementAt",
                                             "(I)Ljava/lang/Object;" );
    jobject result = mpEnv->CallObjectMethod( values, methodID, i );

    return result;
}

jobject JniWrapper::newVector()
{
    jclass vectorClass = mpEnv->FindClass( "java/util/Vector" );
    jmethodID   constructorID = mpEnv->GetMethodID( vectorClass, "<init>", "()V" );
    jobject result = mpEnv->NewObject( vectorClass, constructorID );

    return result;
}

void JniWrapper::addElement( jobject vector, jobject element )
{
    jclass vectorClass = mpEnv->FindClass( "java/util/Vector" );
    jmethodID addElementMethodID = mpEnv->GetMethodID( vectorClass,
                                                       "addElement",
                                                       "(Ljava/lang/Object;)V" );

    mpEnv->CallVoidMethod( vector, addElementMethodID, element );
}

jobject JniWrapper::marshalDoubleVector( const std::vector<double>& rVector )
{
    jobject result = newVector();

    for ( int i = 0; i < rVector.size(); i++ )
    {
          addElement( result, marshalDouble( rVector[i] ) );
    }

    return result;
}

std::pair<std::string, std::string> JniWrapper::unmarshalPairString( jobject vector )
{
    std::pair<std::string, std::string> result;
    result.first  = unmarshalString( (jstring)getVectorElement( vector, 0 ) );
    result.second = unmarshalString( (jstring)getVectorElement( vector, 1 ) );

    return result;
}
""")

test.write(['src', 'jni', 'JniWrapper.h'], """\
#ifndef JniWrapper_h
#define JniWrapper_h

#include <jni.h>
/**
 * Provides routines for dealing with JNI translation etc.
 */

class JniWrapper
{
public:
    JniWrapper( JNIEnv *pEnv );
    JniWrapper( const JniWrapper& rJniWrapper );
    virtual ~JniWrapper();
    JniWrapper& operator=( const JniWrapper& rJniWrapper );


    std::string unmarshalString( jstring value );

    jstring marshalString( const std::string& value );

    jbyteArray marshalByteArray( const std::string& value );

    double unmarshalDouble( jobject value );

    jobject marshalDouble( double value );
    jobject marshallStringVector( const std::vector<std::string>& rMap );

    jobject marshalDoubleVector( const std::vector<double>& rVector );
    std::pair<std::string, std::string> unmarshalPairString( jobject );

protected:
    JNIEnv *mpEnv;

private:
    JniWrapper();
    jobject newVector();
    void addElement( jobject vector, jobject element );
    jobject getVectorElement( jobject values, int i );

};

#endif // JniWrapper_h


""")

test.write(['src', 'jni', 'SConscript'], """\
Import ("env")
denv=env.Copy()

denv.Append(SWIGFLAGS=['-java'])
denv.SharedLibrary('scons',['JniWrapper.cc','Sample.i'])
denv['JARCHDIR']=denv.Dir('.').get_abspath()
denv.Jar(['Sample.i','A.java'])
""")

test.write(['src', 'jni', 'Sample.h'], """\
#include <vector>
#include <iostream>

class SampleTest
{
public:
    std::vector<double> test1( std::pair<std::string, std::string> param )
    {
        std::vector<double> result;
        result.push_back(10);
        return result;
    }
};

""")

test.write(['src', 'jni', 'Sample.i'], """\
%module Sample

%{
#include "Sample.h"
#include "JniWrapper.h"
%}

%typemap(jni)    std::vector<double>, std::vector<double>& "jobject"
%typemap(jtype)  std::vector<double>, std::vector<double>& "java.util.Vector"
%typemap(jstype) std::vector<double>, std::vector<double>& "java.util.Vector"

// return a Vector of Doubles
%typemap(javaout) std::vector<double> {
    return $jnicall;
}
%typemap(out) std::vector<double> {
    JniWrapper JniWrapper(jenv);
    $result = JniWrapper.marshalDoubleVector( $1 );
}

/*********************************************************************
 *
 * Pairs of String (IN/OUT)
 *
 *********************************************************************/
%typemap(jni)     std::pair<std::string, std::string>, const std::pair<std::string, std::string>& "jobject"
%typemap(jtype)   std::pair<std::string, std::string>, const std::pair<std::string, std::string>&  "java.util.Vector"
%typemap(jstype)  std::pair<std::string, std::string>, const std::pair<std::string, std::string>&  "java.util.Vector"
%typemap(javain)  std::pair<std::string, std::string>, const std::pair<std::string, std::string>&  "$javainput"

// pass in by reference a Vector of std::string
%typemap(in) const std::pair<std::string, std::string>&   {
    $1 = new std::pair<std::string, std::string>();
    JniWrapper JniWrapper(jenv);
    *($1) = JniWrapper.unmarshalPairString( $input );
}

//cleanup
%typemap(freearg) const std::pair<std::string, std::string>& {
    delete $1;
}

%include "Sample.h"

// generate:Sample.java
// generate:SampleJni.java
// generate:SampleTest.java
""")

test.write(['src', 'server', 'JavaSource', 'SConscript'], """\
import os
Import ("env")
classes=env.Java(target='classes',source=['com'])

HelloApplet=os.path.join('#/buildout/HelloApplet/HelloApplet.jar')
env['WARXFILES']=['SConscript','.cvsignore']
env['WARXDIRS']=['CVS']
#env.War('scons',[classes,Dir('../WebContent'),HelloApplet])
""")

test.write(['src', 'server', 'JavaSource', 'com', 'gnu', 'scons', 'web', 'tools', 'Bool.java'], """\
package com.gnu.scons.web.tools;
public class Bool {
    boolean flag;

    public Bool()
    {
        flag = false;
    }

    public Bool( boolean aFlag )
    {
        flag = aFlag;
    }

    public boolean booleanValue()
    {
        return flag;
    }
}
""")

test.write(['src', 'server', 'JavaSource', 'com', 'gnu', 'scons', 'web', 'tools', 'StringUtils.java'], """\
package com.gnu.scons.web.tools;

import java.util.Iterator;
import java.util.Map;

public class StringUtils
{
    public static String toPercent( String value )
    {
        if ( value.equals("") )
        {
            return "";
        }
        else
        {
            return value + "%";
        }
    }

}
""")

test.write(['src', 'server', 'WebContent', 'index.html'], """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<HTML>
<HEAD>
<META http-equiv="refresh" content="0;URL=go?action=home">
<TITLE>index.html</TITLE>
</HEAD>
<BODY>
<P><a href="go?action=home">go?action=home</a></P>
</BODY>
</HTML>
""")

test.write(['src', 'server', 'WebContent', 'META-INF', 'MANIFEST.MF'], """\
Manifest-Version: 1.0
Class-Path:

""")

test.write(['src', 'server', 'WebContent', 'WEB-INF', 'web.xml'], """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE web-app PUBLIC "-//Sun Microsystems, Inc.//DTD Web Application 2.3//EN" "http://java.sun.com/dtd/web-app_2_3.dtd">
<web-app id="WebExample">
    <display-name>scons</display-name>
    <servlet>
        <servlet-name>WebExample</servlet-name>
        <display-name>WebExample</display-name>
        <servlet-class>com.gnu.scons.web.tool.WebExample</servlet-class>
    </servlet>
    <servlet-mapping>
        <servlet-name>WebExample</servlet-name>
        <url-pattern>/go</url-pattern>
    </servlet-mapping>
    <welcome-file-list>
        <welcome-file>index.html</welcome-file>
        <welcome-file>index.htm</welcome-file>
    </welcome-file-list>
</web-app>
""")

test.write(['src', 'server', 'WebContent', 'WEB-INF', 'conf', 'app.properties'], """\
logging = webExample.Example
""")

test.write(['src', 'server', 'WebContent', 'theme', 'Master.css'], """\
body
{
    font-family: Helvetica,Sans-Serif;
    font-size: 11pt;
}
""")

test.run(arguments = '.')

test.must_exist(['buildout', 'javah', 'myid.jar'])
test.must_exist(['buildout', 'javah', 'MyID', 'MyID.class'])

test.must_exist(['buildout', 'jni', 'Sample.class'])
test.must_exist(['buildout', 'jni', 'Sample.java'])
test.must_exist(['buildout', 'jni', 'SampleJNI.class'])
test.must_exist(['buildout', 'jni', 'SampleJNI.java'])
test.must_exist(['buildout', 'jni', 'SampleTest.class'])
test.must_exist(['buildout', 'jni', 'SampleTest.java'])

test.up_to_date(arguments = '.')

test.pass_test()
