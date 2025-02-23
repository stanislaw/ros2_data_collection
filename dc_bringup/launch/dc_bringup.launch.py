import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import LoadComposableNodes, Node, SetParameter
from launch_ros.descriptions import ComposableNode
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    # Get the launch directory
    bringup_dir = get_package_share_directory("dc_bringup")

    namespace = LaunchConfiguration("namespace")
    use_sim_time = LaunchConfiguration("use_sim_time")
    autostart = LaunchConfiguration("autostart")
    dc_params_file = LaunchConfiguration("dc_params_file")
    use_composition = LaunchConfiguration("use_composition")
    container_name = LaunchConfiguration("container_name")
    use_respawn = LaunchConfiguration("use_respawn")
    log_level = LaunchConfiguration("log_level")
    detection_barcodes_service = LaunchConfiguration("detection_barcodes_service")
    draw_img_service = LaunchConfiguration("draw_img_service")
    save_img_service = LaunchConfiguration("save_img_service")
    group_node = LaunchConfiguration("group_node")

    lifecycle_nodes = ["measurement_server", "destination_server"]

    # Create our own temporary YAML files that include substitutions
    param_substitutions = {"autostart": autostart}

    configured_params = RewrittenYaml(
        source_file=dc_params_file,
        root_key=namespace,
        param_rewrites=param_substitutions,
        convert_types=True,
    )

    stdout_linebuf_envvar = SetEnvironmentVariable("RCUTILS_LOGGING_BUFFERED_STREAM", "1")

    declare_namespace_cmd = DeclareLaunchArgument(
        "namespace", default_value="", description="Top-level namespace"
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="False",
        description="Use simulation (Gazebo) clock if true",
    )

    declare_params_file_cmd = DeclareLaunchArgument(
        "dc_params_file",
        default_value=os.path.join(bringup_dir, "params", "dc_params.yaml"),
        description="Full path to the ROS2 parameters file to use for all launched nodes",
    )

    declare_autostart_cmd = DeclareLaunchArgument(
        "autostart",
        default_value="True",
        description="Automatically startup the dc stack",
    )

    declare_use_composition_cmd = DeclareLaunchArgument(
        "use_composition",
        default_value="True",
        description="Use composed bringup if True",
    )

    declare_container_name_cmd = DeclareLaunchArgument(
        "container_name",
        default_value="dc_container",
        description="the name of container that nodes will load in if use composition",
    )

    declare_use_respawn_cmd = DeclareLaunchArgument(
        "use_respawn",
        default_value="False",
        description="Whether to respawn if a node crashes. Applied when composition is disabled.",
    )

    declare_log_level_cmd = DeclareLaunchArgument(
        "log_level", default_value="info", description="log level"
    )

    declare_detection_barcodes_service = DeclareLaunchArgument(
        "detection_barcodes_service",
        default_value="False",
        description="Start barcode detection service",
    )
    declare_draw_img_service = DeclareLaunchArgument(
        "draw_img_service", default_value="False", description="Start draw image service"
    )
    declare_save_img_service = DeclareLaunchArgument(
        "save_img_service", default_value="False", description="Start save image service"
    )
    declare_group_node = DeclareLaunchArgument(
        "group_node", default_value="False", description="Start group_node"
    )

    load_nodes = GroupAction(
        condition=IfCondition(PythonExpression(["not ", use_composition])),
        actions=[
            SetParameter("use_sim_time", use_sim_time),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("dc_services"),
                        "launch",
                        "dc_save_image.launch.py",
                    )
                ),
                condition=IfCondition(save_img_service),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("dc_services"),
                        "launch",
                        "dc_draw_image.launch.py",
                    )
                ),
                condition=IfCondition(draw_img_service),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("dc_services"),
                        "launch",
                        "dc_detection_barcodes.launch.py",
                    )
                ),
                condition=IfCondition(detection_barcodes_service),
            ),
            Node(
                package="dc_measurements",
                executable="measurement_server",
                name="measurement_server",
                output={
                    "stdout": "screen",
                    "stderr": "screen",
                },
                respawn=use_respawn,
                respawn_delay=2.0,
                parameters=[configured_params],
                arguments=["--ros-args", "--log-level", log_level],
            ),
            Node(
                condition=IfCondition(group_node),
                package="dc_group",
                executable="group_server",
                output={
                    "stdout": "screen",
                    "stderr": "screen",
                },
                parameters=[configured_params],
                arguments=["--ros-args", "--log-level", log_level],
            ),
            Node(
                package="dc_destinations",
                executable="destination_server",
                name="destination_server",
                output={
                    "stdout": "screen",
                    "stderr": "screen",
                },
                respawn=use_respawn,
                respawn_delay=2.0,
                parameters=[configured_params],
                arguments=["--ros-args", "--log-level", log_level],
            ),
            Node(
                package="nav2_lifecycle_manager",
                executable="lifecycle_manager",
                name="lifecycle_manager_navigation",
                output={
                    "stdout": "screen",
                    "stderr": "screen",
                },
                arguments=["--ros-args", "--log-level", log_level],
                parameters=[
                    {"autostart": autostart},
                    {"node_names": lifecycle_nodes, "bond_timeout": 10.0},
                ],
            ),
        ],
    )

    load_composable_nodes = GroupAction(
        condition=IfCondition(use_composition),
        actions=[
            SetParameter("use_sim_time", use_sim_time),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("dc_services"),
                        "launch",
                        "dc_save_image.launch.py",
                    )
                ),
                condition=IfCondition(save_img_service),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("dc_services"),
                        "launch",
                        "dc_draw_image.launch.py",
                    )
                ),
                condition=IfCondition(draw_img_service),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("dc_services"),
                        "launch",
                        "dc_detection_barcodes.launch.py",
                    )
                ),
                condition=IfCondition(detection_barcodes_service),
            ),
            Node(
                condition=IfCondition(use_composition),
                name=container_name,
                package="rclcpp_components",
                executable="component_container_isolated",
                parameters=[configured_params, {"autostart": autostart}],
                arguments=["--ros-args", "--log-level", log_level],
                output="screen",
            ),
            Node(
                condition=IfCondition(group_node),
                package="dc_group",
                executable="group_server",
                output={
                    "stdout": "screen",
                    "stderr": "screen",
                },
                parameters=[configured_params],
                arguments=["--ros-args", "--log-level", log_level],
            ),
            LoadComposableNodes(
                target_container=container_name,
                composable_node_descriptions=[
                    ComposableNode(
                        package="dc_measurements",
                        plugin="measurement_server::MeasurementServer",
                        name="measurement_server",
                        parameters=[configured_params],
                    ),
                    ComposableNode(
                        package="dc_destinations",
                        plugin="destination_server::DestinationServer",
                        name="destination_server",
                        parameters=[configured_params],
                    ),
                    ComposableNode(
                        package="nav2_lifecycle_manager",
                        plugin="nav2_lifecycle_manager::LifecycleManager",
                        name="lifecycle_manager_navigation",
                        parameters=[
                            {
                                "autostart": autostart,
                                "node_names": lifecycle_nodes,
                                "bond_timeout": 10.0,
                            }
                        ],
                    ),
                ],
            ),
        ],
    )

    # Create the launch description and populate
    ld = LaunchDescription()

    # Set environment variables
    ld.add_action(stdout_linebuf_envvar)

    # Declare the launch options
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(declare_autostart_cmd)
    ld.add_action(declare_use_composition_cmd)
    ld.add_action(declare_container_name_cmd)
    ld.add_action(declare_use_respawn_cmd)
    ld.add_action(declare_log_level_cmd)
    ld.add_action(declare_detection_barcodes_service)
    ld.add_action(declare_draw_img_service)
    ld.add_action(declare_save_img_service)
    ld.add_action(declare_group_node)
    # Add the actions to launch all of the navigation nodes
    ld.add_action(load_nodes)
    ld.add_action(load_composable_nodes)

    return ld
