# Compatibility shim for Material Maker 1.7's asynchronous renderer startup.
# The upstream _ready() starts device creation without waiting for it, while
# startup shaders immediately read rendering_device. Lavapipe exposes this race.
# Keep all rendering on the original dedicated thread and wait for initialization.
extends "res://addons/material_maker/engine/multi_renderer.gd"

func initialize_rendering_thread():
	rendering_thread = Thread.new()
	rendering_mutex = Mutex.new()
	rendering_semaphore = Semaphore.new()
	var initialized := Semaphore.new()
	rendering_thread.start(func():
		create_rendering_device()
		initialized.post()
		thread_loop()
	, 2)
	initialized.wait()
	if rendering_device == null:
		push_error("Material Maker could not initialize its Vulkan compute device")
		get_tree().quit(2)
	else:
		print("MATERIAL_MAKER_COMPUTE_READY")
