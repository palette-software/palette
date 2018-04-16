# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
""" WSGI servers - non-middleware - included with the `akiri.framework`."""
import pkg_resources
pkg_resources.declare_namespace(__name__)

from .map import MapApplication
