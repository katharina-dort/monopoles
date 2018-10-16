#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import math
import numpy as np
from numpy.linalg import eig, inv
from basf2 import *

# Some ROOT tools
import ROOT
from ROOT import Belle2
from ROOT import gROOT, AddressOf


from rawdata import add_unpackers
from reconstruction import *
from simulation import *
import os.path
from cdc.cr import *

reset_database()
use_database_chain()
use_central_database("data_reprocessing_prod5", LogLevel.WARNING)
use_local_database("localDB/database.txt", "localDB")



# Define a ROOT struct to hold output data in the TTree.
gROOT.ProcessLine('struct EventDataSimHit {\
    int exp;\
    int run;\
    int evt;\
    int vxd_id;\
    int layer;\
    int ladder;\
    int sensor;\
    int simhit_PDGcode;\
    float cls_u;\
    float cls_v;\
    float cls_w;\
    float cls_x;\
    float cls_y;\
    float cls_z;\
	int cls_uSize;\
	int cls_vSize;\
    float charge;\
    float seed_charge;\
};'
                  )

from ROOT import EventDataSimHit



class VXDHitPosition(Module):

	"""
	A simple module to check the simulation of PXDTrueHits with Geant4 steps.
	This module writes its output to a ROOT tree.
	Primary goal is supporting of validation plots
	"""



	def __init__(self):
		"""Initialize the module"""

		super(VXDHitPosition, self).__init__()
		## Output ROOT file.
		self.file = ROOT.TFile('out.root',
				               'recreate')
		self.tree = ROOT.TTree('tree', '')
		self.data = EventDataSimHit()
		# Declare tree branches
		for key in EventDataSimHit.__dict__.keys():
			if not '__' in key:
				formstring = '/F'
				if isinstance(self.data.__getattribute__(key), int):
					formstring = '/I'
				self.tree.Branch(key, AddressOf(self.data, key), key
						         + formstring)

	def beginRun(self):
		""" Does nothing """

	def event(self):
		geoCache = Belle2.VXD.GeoCache.getInstance()

		pxd_clusters = Belle2.PyStoreArray('PXDClusters')

		#print("event=", Belle2.PyStoreObj('EventMetaData').obj().getEvent())
		for cluster in pxd_clusters:
			# Event identification
			self.data.exp = Belle2.PyStoreObj('EventMetaData').obj().getExperiment()
			self.data.run = Belle2.PyStoreObj('EventMetaData').obj().getRun()
			self.data.evt = Belle2.PyStoreObj('EventMetaData').obj().getEvent()

			# Sensor identification
			vxd_id = cluster.getSensorID()
			self.data.vxd_id = vxd_id.getID()
			self.data.layer = vxd_id.getLayerNumber()
			self.data.ladder = vxd_id.getLadderNumber()
			self.data.sensor = vxd_id.getSensorNumber()

			#Find digits in cluster
			digits = cluster.getRelationsTo('PXDDigits')
			mc_part = cluster.getRelationsTo('MCParticles')
			true_parts = cluster.getRelationsTo('PXDTrueHits')
			sim_parts0 = cluster.getRelationsTo('PXDSimHits')

                	print(len(digits))

			info = geoCache.get(vxd_id)
			r_local = ROOT.TVector3(cluster.getU(), cluster.getV(), 0)
			r_global = info.pointToGlobal(r_local)

			self.data.cls_u = r_local.X()
			self.data.cls_v = r_local.Y()
			self.data.cls_w = r_local.Z()
			self.data.cls_x = r_global.X()
			self.data.cls_y = r_global.Y()
			self.data.cls_z = r_global.Z()


			# Cluster size and charge
			self.data.cls_uSize = cluster.getUSize()
			self.data.cls_vSize = cluster.getVSize()
			self.data.charge = cluster.getCharge()
			self.data.seed_charge = cluster.getSeedCharge()


			# Fill tree
			self.file.cd()
			self.tree.Fill()

	def terminate(self):
		""" Close the output file."""

		self.file.cd()
		self.file.Write()
		self.file.Close()

main = create_path()
main.add_module('RootInput',inputFileName = '/home/belle2/kdort/simulations/monopoles_sim/MonopolePairCust_4GeV.root')
# Load parameters
main.add_module(register_module('Gearbox'))
# Create geometry
main.add_module(register_module('Geometry'))
main.add_module(VXDHitPosition())
process(main)
print(statistics)
