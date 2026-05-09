cmake_minimum_required(VERSION 3.8)
project(echo_voice_ai)

find_package(ament_cmake REQUIRED)

foreach(dir launch config maps firmware)
  if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/${dir}")
    install(DIRECTORY ${dir}/
      DESTINATION share/${PROJECT_NAME}/${dir})
  endif()
endforeach()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/scripts")
  install(DIRECTORY scripts/
    DESTINATION share/${PROJECT_NAME}/scripts)

  file(GLOB SCRIPT_FILES
    "${CMAKE_CURRENT_SOURCE_DIR}/scripts/*.py"
    "${CMAKE_CURRENT_SOURCE_DIR}/scripts/*.sh")

  if(SCRIPT_FILES)
    install(PROGRAMS ${SCRIPT_FILES}
      DESTINATION lib/${PROJECT_NAME})
  endif()
endif()

ament_package()
