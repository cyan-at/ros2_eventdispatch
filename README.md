bloom toolchain:

https://docs.ros.org/en/jazzy/How-To-Guides/Releasing/First-Time-Release.html

* [PR 907](https://github.com/ros2-gbp/ros2-gbp-github-org/issues/907)
* [PR 908](https://github.com/ros2-gbp/ros2-gbp-github-org/issues/908)

https://robotics.stackexchange.com/a/117904/53773

```
bloom-release --new-track --rosdistro jazzy --track jazzy ros2_eventdispatch
```

https://github.com/ros2-gbp/ros2_eventdispatch-release.git

https://github.com/cyan-at/ros2_eventdispatch.git

for 'amending' a tag:
```
git tag 0.2.25 2c4bf0ca5263accd5a661051994e0913de361621 -f
git push origin refs/tags/0.2.25 --force
```