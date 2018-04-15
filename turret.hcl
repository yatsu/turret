kernel "py_kernel" {
  pass_env = ["PATH"]
}

app "watchdog" {
  class  = "turret.app.watchdog.WatchdogApp"
  kernel = "py_kernel"

  logger {
    level = "info"
  }

  options {
    handlers = [
      {
        patterns           = ["*.py"]
        ignore_patterns    = ["*/examples/*.py"]
        ignore_directories = true

        functions = [
          "pytest.handle_watchdog_event({event})",
        ]

        throttle = 0.5
      },
    ]
  }
}

app "pytest" {
  class  = "turret.app.pytest.PyTestRunnerApp"
  kernel = "py_kernel"

  logger {
    level = "info"
  }

  options {
    args = ["-s", "-v", "--color=yes"]

    auto_test = [
      "turret/tests/**/test_*.py",
    ]

    auto_test_map {
      "turret/**/*.py" = "turret/tests/unit/{}/test_{}.py"
    }
  }
}
