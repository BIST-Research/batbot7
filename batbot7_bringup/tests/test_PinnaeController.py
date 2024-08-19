"""
Author: Mason Lopez
Date: 2/2/2024
Purpose: tests the PinnaeController class
    """
    
import unittest

import sys,os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# sys.path.insert("../")
from batbot7_bringup.src.batbot7_bringup.pinnae import PinnaeController, NUM_PINNAE_MOTORS



class TestClass(unittest.TestCase):
    
    def test_default_motor_limits(self):
        pinnae = PinnaeController()
        for i in range(NUM_PINNAE_MOTORS):
            [min_val,max_val] = pinnae.get_motor_limit(i)
            self.assertEqual(min_val,-180)    
            self.assertEqual(max_val,180)  
            
    def test_default_angle(self):
        pinnae = PinnaeController()
        for i in range(NUM_PINNAE_MOTORS):
            self.assertEqual(pinnae.current_angles[i],0)
    
    def test_set_motor_limits(self):
        pinnae = PinnaeController()
        
        for i in range(NUM_PINNAE_MOTORS):
            pinnae.set_motor_limit(i,-100,100)
            [min_val,max_val] = pinnae.get_motor_limit(i)
            self.assertEqual(min_val,-100)    
            self.assertEqual(max_val,100)   
            
    def test_set_motor_min_limit(self):
        pinnae = PinnaeController()
        
        for i in range(NUM_PINNAE_MOTORS):
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
        
        for i in range(NUM_PINNAE_MOTORS):
            self.assertFalse(pinnae.set_motor_max_limit(i,-1))
            self.assertTrue(pinnae.set_motor_max_limit(i,0))
            self.assertTrue(pinnae.set_motor_max_limit(i,1))
            
            # change new limit
            self.assertTrue(pinnae.set_motor_angle(i,-1))
            self.assertTrue(pinnae.set_motor_max_limit(i,1))
            self.assertTrue(pinnae.set_motor_max_limit(i,0))
            self.assertTrue(pinnae.set_motor_max_limit(i,-1))
            self.assertFalse(pinnae.set_motor_max_limit(i,-2))
            
    def test_set_motor_limit(self):
        pinnae = PinnaeController()
        
        # default angle is 0
        for i in range(NUM_PINNAE_MOTORS):
            self.assertTrue(pinnae.set_motor_limit(i,-100,100))
            self.assertTrue(pinnae.set_motor_limit(i,0,100))
            self.assertTrue(pinnae.set_motor_limit(i,-100,0))
            
            self.assertFalse(pinnae.set_motor_limit(i,10,100))
            self.assertFalse(pinnae.set_motor_limit(i,-100,-1))
            
            # change the motor angle
            self.assertTrue(pinnae.set_motor_angle(i,-10))
            self.assertTrue(pinnae.set_motor_limit(i,-100,-9))
            self.assertTrue(pinnae.set_motor_limit(i,-100,-10))
            
            self.assertFalse(pinnae.set_motor_limit(i,-8,100))
            self.assertFalse(pinnae.set_motor_limit(i,-100,-11))
            
            
    def test_set_motor_angle(self):
        pinnae = PinnaeController()
        
        # default angle is 0 
        # default min angle is -180
        # default max angle is 180
        for i in range(NUM_PINNAE_MOTORS):
            self.assertTrue(pinnae.set_motor_angle(i,1))
            self.assertEqual(pinnae.current_angles[i],1)
            self.assertTrue(pinnae.set_motor_angle(i,-1))
            self.assertEqual(pinnae.current_angles[i],-1)
            self.assertTrue(pinnae.set_motor_angle(i,0))
            self.assertEqual(pinnae.current_angles[i],0)
            self.assertTrue(pinnae.set_motor_angle(i,-180))
            self.assertEqual(pinnae.current_angles[i],-180)
            self.assertTrue(pinnae.set_motor_angle(i,180))
            self.assertEqual(pinnae.current_angles[i],180)
            
            self.assertFalse(pinnae.set_motor_angle(i,-181))
            self.assertFalse(pinnae.set_motor_angle(i,181))
            self.assertFalse(pinnae.set_motor_angle(i,200))
            self.assertFalse(pinnae.set_motor_angle(i,-200))
            self.assertEqual(pinnae.current_angles[i],180)
        
    def test_set_motor_angles(self):
        pinnae = PinnaeController()
        
        # default angle is 0 
        # default min angle is -180
        # default max angle is 180
        self.assertFalse(pinnae.set_motor_angles(10))
        self.assertFalse(pinnae.set_motor_angles([181,0,0,0,0,0,0]))
        self.assertFalse(pinnae.set_motor_angles([-181,0,0,0,0,0,0]))
        
        self.assertTrue(pinnae.set_motor_angles([0,0,0,0,0,0,0]))
        self.assertTrue(pinnae.set_motor_angles([180,0,0,0,0,180,0]))
        
        # change the limit
        self.assertTrue(pinnae.set_motor_max_limit(0,200))
        self.assertTrue(pinnae.set_motor_angles([200,0,0,0,0,180,0]))
        self.assertFalse(pinnae.set_motor_angles([201,0,0,0,0,180,0]))
        self.assertTrue(pinnae.set_motor_angles([-180,0,0,0,0,0,180]))
        
        self.assertTrue(pinnae.set_motor_min_limit(0,-300))
        self.assertTrue(pinnae.set_motor_angles([-181,0,0,0,0,0,180]))
        self.assertTrue(pinnae.set_motor_angles([-300,0,0,0,0,0,180]))
        self.assertFalse(pinnae.set_motor_angles([-301,0,0,0,0,0,180]))
        
    
    def test_new_zero_position(self):
        pinnae = PinnaeController()
        
        for i in range(NUM_PINNAE_MOTORS):
            self.assertTrue(pinnae.set_motor_angle(i,30))
            self.assertEqual(pinnae.current_angles[i],30)
            pinnae.set_new_zero_position(i)
            self.assertEqual(pinnae.current_angles[i],0)
            
            self.assertTrue(pinnae.set_motor_angle(i,180))
            self.assertEqual(pinnae.current_angles[i],180)
            pinnae.set_new_zero_position(i)
            self.assertEqual(pinnae.current_angles[i],0)
            
            self.assertTrue(pinnae.set_motor_angle(i,-180))
            self.assertEqual(pinnae.current_angles[i],-180)
            pinnae.set_new_zero_position(i)
            self.assertEqual(pinnae.current_angles[i],0)


    def test_set_motor_to_max(self):
        pinnae = PinnaeController()
        
        for i in range(NUM_PINNAE_MOTORS):
            self.assertFalse(pinnae.current_angles[i] == pinnae.max_angle_limits[i])
            pinnae.set_motor_to_max(i)
            self.assertEqual(pinnae.current_angles[i],pinnae.max_angle_limits[i])
           
            self.assertTrue(pinnae.current_angles[i] == pinnae.max_angle_limits[i])
            pinnae.set_motor_to_max(i)
            self.assertEqual(pinnae.current_angles[i],pinnae.max_angle_limits[i])
    
    def test_set_motors_to_max(self):
        pinnae = PinnaeController()
        
        self.assertFalse(np.array_equal(pinnae.current_angles,pinnae.max_angle_limits))
        pinnae.set_motors_to_max()
        self.assertTrue(np.array_equal(pinnae.current_angles,pinnae.max_angle_limits))
    
    def test_set_motor_to_min(self):
        pinnae = PinnaeController()
        
        for i in range(NUM_PINNAE_MOTORS):
            self.assertFalse(pinnae.current_angles[i] == pinnae.min_angle_limits[i])
            pinnae.set_motor_to_min(i)
            self.assertEqual(pinnae.current_angles[i],pinnae.min_angle_limits[i])
           
            self.assertTrue(pinnae.current_angles[i] == pinnae.min_angle_limits[i])
            pinnae.set_motor_to_min(i)
            self.assertEqual(pinnae.current_angles[i],pinnae.min_angle_limits[i])
    
    def test_set_motors_to_min(self):
        pinnae = PinnaeController()
        
        self.assertFalse(np.array_equal(pinnae.current_angles,pinnae.min_angle_limits))
        pinnae.set_motors_to_min()
        self.assertTrue(np.array_equal(pinnae.current_angles,pinnae.min_angle_limits))
        
        
    def test_set_motor_to_zero(self):
        pinnae = PinnaeController()
        
        for i in range(NUM_PINNAE_MOTORS):
            pinnae.set_motor_angle(i,10)
            self.assertTrue(pinnae.current_angles[i] == 10)
            pinnae.set_motor_to_zero(i)
            self.assertEqual(pinnae.current_angles[i],0)

            
    
    def test_set_motors_to_zero(self):
        pinnae = PinnaeController()
        
        pinnae.set_motors_to_max()
        self.assertTrue(np.array_equal(pinnae.current_angles,pinnae.max_angle_limits))
        pinnae.set_motors_to_zero()
        self.assertFalse(np.array_equal(pinnae.current_angles,pinnae.max_angle_limits))
        
        for i in range(NUM_PINNAE_MOTORS):
            self.assertEqual(pinnae.current_angles[i],0)
            
        # set min to above zero this should not work
        # angle set to 10
        for i in range(NUM_PINNAE_MOTORS):
            self.assertTrue(pinnae.set_motor_angle(i,10))
            self.assertTrue(pinnae.set_motor_min_limit(i,10))
            
        self.assertFalse(pinnae.set_motors_to_zero())
        self.assertTrue(pinnae.set_motor_min_limit(0,-100))
        self.assertFalse(pinnae.set_motors_to_zero())
        
    def test_set_motor_to_zero(self):
        pinnae = PinnaeController()
        
        for i in range(NUM_PINNAE_MOTORS):
            self.assertTrue(pinnae.set_motor_angle(i,10))
            self.assertTrue(pinnae.set_motor_min_limit(i,10))
            self.assertFalse(pinnae.set_motor_to_zero(i))
            
            self.assertTrue(pinnae.set_motor_min_limit(i,-10))
            self.assertTrue(pinnae.set_motor_angle(i,-10))
            self.assertTrue(pinnae.set_motor_to_zero(i))

            
            
            
        
            
        
            
            
            
if __name__ == '__main__':
    unittest.main()