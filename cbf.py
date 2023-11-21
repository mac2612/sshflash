#!/usr/bin/env python3
##############################################################################
#    OpenLFConnect
#
#    Copyright (c) 2012 Jason Pruitt <jrspruitt@gmail.com>
#
#    This file is part of OpenLFConnect.
#    OpenLFConnect is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    OpenLFConnect is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with OpenLFConnect.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################



##############################################################################
# Title:   OpenLFConnect
# Author:  Jason Pruitt
# Email:   jrspruitt@gmail.com
# IRC:     #didj irc.freenode.org
# Wiki:    http://elinux.org/LeapFrog_Pollux_Platform:_OpenLFConnect
##############################################################################

#@
# cbf.py Version 0.1.2
# Ported to Python 3 by A.Mccarthy
#

import os
import array
import struct

#############################
# NOTES:
# kernel_load and kernel_jump
# newest make_cbf.py uses 0x8000
# old one has 0x100000
# latest cbf still have old number
##############################

PACKET_SIZE = 16384
MAGIC_NUMBER = b'\xf0\xde\xbc\x9a'
# MAGIC_NUMBER = struct.pack('IIII', 240, 222, 188, 154)
COMPRESSION_SIG = b'\x1F\x8B\x08\x00' #gunzip
CBF_VERSION = 1
BLOCK_SIZE = 0x20000
KERNEL_LOAD_08 = 0x8000
KERNEL_JUMP_08 = KERNEL_LOAD_08
KERNEL_LOAD_10 = 0x100000
KERNEL_JUMP_10 = KERNEL_LOAD_10
KERNEL_LOAD_28 = 0x00208000
KERNEL_JUMP_28 = KERNEL_LOAD_28

def error(e):
	assert False, e

def check(path, ret_bool=False):
	try:
		if not os.path.exists(path):
			error('Firmware not found')
		else:	
			f = open(path, 'rb')
			file_size = len(f.read())
			f.seek(0)
			magic = f.read(4)
			f.close()
			
			# if not str(file_size/PACKET_SIZE).isdigit():
			if (file_size % PACKET_SIZE) != 0:
				if ret_bool:
					return False
				else:
					error('File is the wrong size, should be multiple of %s.' % str(file_size/PACKET_SIZE))

			if magic != MAGIC_NUMBER:
				if ret_bool:
					return False
				else:
					error('File failed CBF Magic Number check.')
			else:
				return True
	except Exception as e:
		error(e)



def extract(path):
	p = parse(path)
	image = p.get_image()
	
	if p.is_compressed:
		kernel_name = 'zImage'
	else:
		kernel_name = 'Image'

	kernel_path = os.path.join(os.path.dirname(path), kernel_name)
	
	print('Unwrapping Kernel from CBF')

	fimg = open(kernel_path, 'wb')
	fimg.write(image)
	fimg.close()
	print('Saved as: %s' % kernel_name)


def create(mem, opath, ipath):
	try:
		image_name = os.path.basename(ipath)
		image_path = os.path.dirname(ipath)

		if not mem in ('superhigh', 'high', 'low'):
			error('Memory location should be high or low')

		if not opath:
			error('No output file selected.')
		
		if not ipath:
			error('No output file selected')

		if not os.path.exists(ipath):
			error('CBF: Path does not exist.')
		elif os.path.isdir(ipath):
			error('Path is not a file.')
		elif 'zImage' not in image_name and 'Image' not in image_name:
			error('Does not appear to be an Image or zImage file.')
		
		if len(os.path.basename(opath)) > 64:
			error('Output name is too long.')
		
		if not opath.endswith('.cbf'):
			opath = '%s.cbf' % opath

		p = packer(mem, opath, ipath)
		p.pack()
		summary(os.path.join(image_path, opath))
	except Exception as e:
		error(e)


def summary(path):
	check(path)
	p = parse(path)
	p.create_summary()

	print('CBF File Summary:')
	
	for k,v in p.summary.items():
		if len(k) < 7:
			tab = '\t\t'
		else:
			tab = '\t'
		print('%s:%s0x%08x' % (k,tab,v))
		
	print('Compressed: \t %s' % p.is_compressed)



class parse(object):
	def __init__(self, path):
		if os.path.isdir(path):
			error('Path is not a file.')
			
		self._path = path
		self._word_width = 4
		self._summary_names = ['cbf_magic','cbf_version','kernel_load','kernel_jump','size','sum_crc','kernel_crc']
		self._kernel_offset = self._word_width * (len(self._summary_names) - 1)
		self.summary = {}
		self._u32 = struct.Struct("<L")
		self.is_compressed = False



	def error(self, e):
		assert False, e



	def create_summary(self):
		self.get_image()



	def get_image(self):
		try:
			if not check(self._path, True):
				self.error('Problem with file.')
			
			f = open(self._path, 'rb')
	
			for i in range(0, len(self._summary_names)):
				offset = i * self._word_width
				f.seek(offset)
				read_buf = self._u32.unpack(f.read(self._word_width))[0]
				self.summary[self._summary_names[i]] = read_buf
	
			f.seek(self._kernel_offset + self.summary['size'])
			read_buf = self._u32.unpack(f.read(self._word_width))[0]
			self.summary['kernel_crc'] = read_buf
	
			f.seek(self._kernel_offset)
			image = f.read(self.summary['size'])

			if COMPRESSION_SIG in image:
				self.is_compressed = True
	
			f.close()
			return image
		except Exception as e:
			self.error(e)




class packer(object):
	def __init__(self, mem, opath, ipath):
		self._in_path = ipath
		self._out_path = opath
		self._summary = b''
		self._summary_crc = b''
		self._buffer = b''
		self._buffer_crc = b''
		self._size = 0 
		if mem.lower() == 'superhigh':
			self._kernel_jump = KERNEL_JUMP_28
			self._kernel_load = KERNEL_LOAD_28
		elif mem.lower() == 'high':
			self._kernel_jump = KERNEL_JUMP_10
			self._kernel_load = KERNEL_LOAD_10
		elif mem.lower() == 'low':
			self._kernel_jump = KERNEL_JUMP_08
			self._kernel_load = KERNEL_LOAD_08
		else:
			self.error('Memory location must be high, or low.')



	def error(self, e):
		assert False, e



	def crc(self, buf):
		a = array.array('I', buf)
		crc = 0;
		
		for c in a:
			crc = 1 + (crc ^ c)

		return crc



	def pack(self):
		try:
			self.set_buffer()
			self.set_summary()
			buf = self._summary
			buf += self._buffer
			buf_len = len(buf)

			rem = buf_len % BLOCK_SIZE
			pad_len = 0
			padding = b''
			
			if rem != 0:
				pad_len = BLOCK_SIZE - rem
				
			padding = pad_len * b'\xFF'
			
			buf += padding
			print('Writing CBF file.')
			f = open(self._out_path, 'wb')
			f.write(buf)
			f.close()
			
			
		except Exception as e:
			error(e)


	
	def set_buffer(self):			
		f = open(self._in_path, 'rb')
		self._buffer = f.read()		
		self._size = len(self._buffer)
		self._buffer_crc = self.crc(self._buffer)
		self._buffer += struct.pack('I', self._buffer_crc & 0xFFFFFFFF)
		f.close



	def set_summary(self):
		if not self._buffer_crc:
			self.error('Pack buffer is empty.')
			
		if not self._size:
			self.error('Pack problem reading buffer for summary.')
			
		self._summary = MAGIC_NUMBER
		self._summary += struct.pack('IIII', CBF_VERSION, self._kernel_load, self._kernel_jump, self._size)
		self._summary_crc = self.crc(self._summary)
		self._summary += struct.pack('I', self._summary_crc)

if __name__ == '__main__':
	print('No examples yet.')
