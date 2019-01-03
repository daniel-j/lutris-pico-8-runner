/* eslint-env browser */

var Module // current Module
var module_canvas
var codo_command = 0
var codo_command_p = 0
var codo_volume = 256
var codo_running = false
var open_fullscreen
var config

function onKeyDown_blocker (event) {
  event = event || window.event

  // only while cartridge is active
  // to do: check for element focus instead

  var o = document.activeElement
  if (!o || o === document.body || o.tagName === 'canvas') {
    if (event.keyCode === 122) {
      // allow F11 to toggle fullscreen
      var isFullscreen = document.webkitIsFullScreen
      if (isFullscreen) document.webkitCancelFullScreen()
      else request_fullscreen()
    }
    if (event.preventDefault) event.preventDefault()
  }
}

function onResize() {
  var w = module_canvas.clientWidth
  var h = module_canvas.clientHeight
  var factor = Math.min(window.innerWidth / w, window.innerHeight / h)
  module_canvas.setAttribute('style', 'width: ' + Math.round(w * factor) +
      'px; height: ' + Math.round(h * factor) + 'px;')
}

function set_sound_button () {
  var sb = document.getElementById('sound_button')

  if (codo_volume === 0) {
    sb.innerHTML = '<img src=gfx/p8b_sound0.png width=24>'
  } else {
    sb.innerHTML = '<img src=gfx/p8b_sound1.png width=24>'
  }
}

function set_pause_button () {
  var sb = document.getElementById('pause_button')

  if (codo_running) {
    sb.innerHTML = '<img src=gfx/p8b_pause.png width=24>'
  } else {
    sb.innerHTML = '<img src=gfx/p8b_resume.png width=24>'
  }
}

function request_fullscreen () {
  playarea_game = document.getElementById('playarea_game')
  playarea_game.webkitRequestFullscreen()
}

var pico8_buttons = [0, 0, 0, 0, 0, 0, 0, 0]

function press_pico8_button (pl, which, state) {
  if (state === 0) { pico8_buttons[pl] &= ~(1 << which) } else { pico8_buttons[pl] |= (1 << which) }
}

function get_cart_info (pid) {
  var num = Math.floor(pid / 10000);
  var url = 'https://www.lexaloffle.com/bbs/cposts/'+num+'/';
  return url + pid + `.p8.png`;
}

function load_cartridge (engine, cartridge) {
  
  if (/^\d+$/.test(cartridge)) {
    cartridge = get_cart_info(cartridge)
  }

  module_canvas = document.getElementById('module_canvas')

  if (Module) {
    codo_command = 6
    codo_command_p = cartridge.match(/(\d*)\.p8\.png/)[1]
    return
  }

  Module = {
    arguments: [cartridge],
    canvas: module_canvas
  }

  var e = document.createElement('script')
  e.type = 'application/javascript'
  e.src = engine

  e.addEventListener('load', function () {
    // override readAsync to add support for loading other carts
    var readAsync = Module.readAsync
    Module.readAsync = function (url) {
      var args = Array.prototype.slice.call(arguments)
      if (url.startsWith('/bbs')) {
        args[0] = 'https://www.lexaloffle.com' + url
        console.log('readAsync', url, '->', args[0])
      } else {
        console.log('readAsync', url)
      }
      readAsync.apply(null, args)
    }

    onResize()
    window.addEventListener('resize', onResize, false)
    setInterval(onResize, 1000 / 10)
    document.getElementById('buttonsdiv').style.display = 'block'

    // install key blocker
    document.addEventListener('keydown', onKeyDown_blocker, false)
  }, false)

  document.body.appendChild(e) // load and run

  codo_running = true
}

function load_config (config) {
  load_cartridge(config.engine, config.cartridge)
  if (config.fullscreen) request_fullscreen()
}

document.addEventListener("visibilitychange", function() {
  if (!Module) return
  // pause game when not visible
  if (document.visibilityState === 'hidden') {
    Module.pauseMainLoop()
  } else {
    if (codo_running && Module.resumeMainLoop) Module.resumeMainLoop()
  }
})

// preload assets
new Image().src = 'gfx/p8b_sound0.png'
new Image().src = 'gfx/p8b_sound1.png'
new Image().src = 'gfx/p8b_pause.png'
new Image().src = 'gfx/p8b_resume.png'
