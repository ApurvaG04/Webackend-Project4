#!/bin/sh

cd ..
mkdir var

cd var
mkdir primary
mkdir secondary_1
mkdir secondary_2

cd primary
mkdir data
mkdir mount
cd ..

cd secondary_1
mkdir mount
mkdir data
cd ..

cd secondary_2
mkdir data
mkdir mount