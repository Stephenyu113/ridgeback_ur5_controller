#!/usr/bin/python

import rospy
import copy
import tf

from interactive_markers.interactive_marker_server import *
from interactive_markers.menu_handler import *
from visualization_msgs.msg import *
from geometry_msgs.msg import Point
from geometry_msgs.msg import Wrench
from tf.broadcaster import TransformBroadcaster

marker_pose = geometry_msgs.msg.Transform()
listener = None
wrench_pub = None

def frameCallback( msg ):
    try:
        listener.waitForTransform("/FT300_link", "/world", rospy.Time(0), rospy.Duration(7.0))
        (trans,rot1) = listener.lookupTransform("/FT300_link", "/world", rospy.Time(0))
        # Publish the fake force
        fake_wrench = geometry_msgs.msg.WrenchStamped()
        fake_wrench.wrench.force.x = trans[0] - marker_pose.translation.x
        fake_wrench.wrench.force.y = trans[1] - marker_pose.translation.y
        fake_wrench.wrench.force.z = trans[2] - marker_pose.translation.z
        rot = (marker_pose.rotation.x, marker_pose.rotation.y,
                marker_pose.rotation.z, marker_pose.rotation.w)
        euler = tf.transformations.euler_from_quaternion(rot)
        fake_wrench.wrench.torque.x = euler[0]
        fake_wrench.wrench.torque.y = euler[1]
        fake_wrench.wrench.torque.z = euler[2]
        fake_wrench.header.frame_id = "FT300_link"
        fake_wrench.header.stamp = rospy.Time(0)
        wrench_pub.publish(fake_wrench)
    except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
        print "Coudn't find transforms!"


def makeBox( msg ):
    marker = Marker()

    marker.type = Marker.SPHERE
    marker.scale.x = msg.scale * 0.02
    marker.scale.y = msg.scale * 0.02
    marker.scale.z = msg.scale * 0.02
    marker.color.r = 0.0
    marker.color.g = 1.0
    marker.color.b = 0.0
    marker.color.a = 1.0

    return marker

def makeBoxControl( msg ):
    control =  InteractiveMarkerControl()
    control.always_visible = True
    control.markers.append( makeBox(msg) )
    msg.controls.append( control )
    return control

def processFeedback(feedback, br):
    s = "Feedback from marker '" + feedback.marker_name
    s += "' / control '" + feedback.control_name + "'"

    mp = ""
    if feedback.mouse_point_valid:
        mp = " at " + str(feedback.mouse_point.x)
        mp += ", " + str(feedback.mouse_point.y)
        mp += ", " + str(feedback.mouse_point.z)
        mp += " in frame " + feedback.header.frame_id

    if feedback.event_type == InteractiveMarkerFeedback.BUTTON_CLICK:
        rospy.loginfo(s + ": button click" + mp + ".")
    elif feedback.event_type == InteractiveMarkerFeedback.MENU_SELECT:
        rospy.loginfo(s + ": menu item " + str(
            feedback.menu_entry_id) + " clicked" + mp + ".")
    elif feedback.event_type == InteractiveMarkerFeedback.POSE_UPDATE:
        rospy.loginfo(s + ": pose changed")
        br.sendTransform((feedback.pose.position.x,
                         feedback.pose.position.y,
                         feedback.pose.position.z),
                         (0, 0, 0, 1),
                         rospy.Time.now(),
                         "fake_force_pose",
                         "world")
        marker_pose.translation.x = feedback.pose.position.x
        marker_pose.translation.y = feedback.pose.position.y
        marker_pose.translation.z = feedback.pose.position.z
        marker_pose.rotation.x = feedback.pose.orientation.x
        marker_pose.rotation.y = feedback.pose.orientation.y
        marker_pose.rotation.z = feedback.pose.orientation.z
        marker_pose.rotation.w = feedback.pose.orientation.w
    elif feedback.event_type == InteractiveMarkerFeedback.MOUSE_DOWN:
        rospy.loginfo(s + ": mouse down" + mp + ".")
    elif feedback.event_type == InteractiveMarkerFeedback.MOUSE_UP:
        rospy.loginfo(s + ": mouse up" + mp + ".")
    server.applyChanges()
    

if __name__ == "__main__":
    rospy.init_node("fake_force_sensor")
    br = TransformBroadcaster()
    listener = tf.TransformListener()
    wrench_pub = rospy.Publisher('/wrench', geometry_msgs.msg.WrenchStamped, queue_size=1)

     # Publisher for the wrench
    rospy.Timer(rospy.Duration(0.02), frameCallback)

    server = InteractiveMarkerServer("fake_force_sensor")
    menu_handler = MenuHandler()
    pf_wrap = lambda fb: processFeedback(fb, br)
    
    menu_handler.insert("First Entry",
                        callback=pf_wrap)
    menu_handler.insert("Second Entry",
                        callback=pf_wrap)
    sub_menu_handle = menu_handler.insert("Submenu")
    menu_handler.insert(
        "First Entry", parent=sub_menu_handle, callback=pf_wrap)
    menu_handler.insert(
        "Second Entry", parent=sub_menu_handle, callback=pf_wrap)

    position = Point(0, 0, 0)

    int_marker = InteractiveMarker()
    int_marker.header.frame_id = "world"
    int_marker.pose.position = position
    int_marker.scale = 1

    int_marker.name = "fake_wrench"
    int_marker.description = "Sim wrench \n Force = vector from UR5 ee to marker \n Torque = angle from initial orientation)"

    # insert a box
    makeBoxControl(int_marker)
    fixed = False
    control = InteractiveMarkerControl()
    control.orientation.w = 1
    control.orientation.x = 1
    control.orientation.y = 0
    control.orientation.z = 0
    control.name = "rotate_x"
    control.interaction_mode = InteractiveMarkerControl.ROTATE_AXIS
    if fixed:
        control.orientation_mode = InteractiveMarkerControl.FIXED
    int_marker.controls.append(control)

    control = InteractiveMarkerControl()
    control.orientation.w = 1
    control.orientation.x = 1
    control.orientation.y = 0
    control.orientation.z = 0
    control.name = "move_x"
    control.interaction_mode = InteractiveMarkerControl.MOVE_AXIS
    if fixed:
        control.orientation_mode = InteractiveMarkerControl.FIXED
    int_marker.controls.append(control)

    control = InteractiveMarkerControl()
    control.orientation.w = 1
    control.orientation.x = 0
    control.orientation.y = 1
    control.orientation.z = 0
    control.name = "rotate_z"
    control.interaction_mode = InteractiveMarkerControl.ROTATE_AXIS
    if fixed:
        control.orientation_mode = InteractiveMarkerControl.FIXED
    int_marker.controls.append(control)

    control = InteractiveMarkerControl()
    control.orientation.w = 1
    control.orientation.x = 0
    control.orientation.y = 1
    control.orientation.z = 0
    control.name = "move_z"
    control.interaction_mode = InteractiveMarkerControl.MOVE_AXIS
    if fixed:
        control.orientation_mode = InteractiveMarkerControl.FIXED
    int_marker.controls.append(control)

    control = InteractiveMarkerControl()
    control.orientation.w = 1
    control.orientation.x = 0
    control.orientation.y = 0
    control.orientation.z = 1
    control.name = "rotate_y"
    control.interaction_mode = InteractiveMarkerControl.ROTATE_AXIS
    if fixed:
        control.orientation_mode = InteractiveMarkerControl.FIXED
    int_marker.controls.append(control)

    control = InteractiveMarkerControl()
    control.orientation.w = 1
    control.orientation.x = 0
    control.orientation.y = 0
    control.orientation.z = 1
    control.name = "move_y"
    control.interaction_mode = InteractiveMarkerControl.MOVE_AXIS
    if fixed:
        control.orientation_mode = InteractiveMarkerControl.FIXED
    int_marker.controls.append(control)

    server.insert(int_marker, pf_wrap)
    menu_handler.apply(server, int_marker.name)

    server.applyChanges()

    rospy.spin()