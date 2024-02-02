"""
Author: Mason Lopez
Date: 2/2/2024
Purpose: tests the PinnaeController class
    """
    
import unittest

import sys,os
# sys.path.insert(0,"tests")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pinnae import PinnaeController

NUM_MOTORS = 6

class TestClass(unittest.TestCase):
    
    def test_default_motor_limits(self):
        pinnae = PinnaeController()
        for i in range(NUM_MOTORS):
            [min_val,max_val] = pinnae.get_motor_limit(i)
            self.assertEqual(min_val,-180)    
            self.assertEqual(max_val,180)  
            
    def test_default_angle(self):
        pinnae = PinnaeController()
        for i in range(NUM_MOTORS):
            self.assertEqual(pinnae.current_angles[i],0)
    
    def test_set_motor_limits(self):
        pinnae = PinnaeController()
        
        for i in range(NUM_MOTORS):
            pinnae.set_motor_limit(i,-100,100)
            [min_val,max_val] = pinnae.get_motor_limit(i)
            self.assertEqual(min_val,-100)    
            self.assertEqual(max_val,100)   
            
    def test_set_motor_min_limit(self):
        pinnae = PinnaeController()
        
        for i in range(NUM_MOTORS):
            self.assertFalse(pinnae.set_motor_min_limit(i,1)) 
            self.assertTrue(pinnae.set_motor_min_limit(i,0))
            self.assertTrue(pinnae.set_motor_min_limit(i,-1))
            
            # change new limit
            self.assertTrue(pinnae.set_motor_angle(i,-1))
            self.assertFalse(pinnae.set_motor_min_limit(i,0))
            self.assertTrue(pinnae.set_motor_min_limit(i,-1))
            self.assertTrue(pinnae.set_motor_min_limit(i,-2))
            
    def test_set_motor_max_limit(self):
        pinnae = PinnaeController()
        
        for i in range(NUM_MOTORS):
            self.assertFalse(pinnae.set_motor_max_limit(i,-1))
            self.assertTrue(pinnae.set_motor_max_limit(i,0))
            self.assertTrue(pinnae.set_motor_max_limit(i,1))
            
            # change new limit
            self.assertTrue(pinnae.set_motor_angle(i,-1))
            self.assertTrue(pinnae.set_motor_max_limit(i,1))
            self.assertTrue(pinnae.set_motor_max_limit(i,0))
            self.assertTrue(pinnae.set_motor_max_limit(i,-1))
            self.assertFalse(pinnae.set_motor_max_limit(i,-2))
            
            
        
            
        
            
            
            
if __name__ == '__main__':
    unittest.main()