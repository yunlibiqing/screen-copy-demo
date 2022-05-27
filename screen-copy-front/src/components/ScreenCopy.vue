<template>
    <div>
      <canvas id="canvas" style="border: 1px solid red;"></canvas>
      <button type="button" @click="audioStart">点击播放</button>
    </div>
</template>

<script>
import PCMPlayer from '../utils/player-pcm'
export default {
  name: 'ScreenCopy',
  data () {
    return {
      socketUri: 'ws://127.0.0.1:9002/',
      canvas: undefined,
      ws: undefined,
      audioWs: undefined,
      width: 0,
      height: 0
    }
  },
  mounted () {
    this.start()
    // this.audioStart()
  },
  beforeDestroy () {
  },
  methods: {
    audioStart () {
      var audioWs = new WebSocket('ws://127.0.0.1:9002/audio')
      var player = new PCMPlayer({
        encoding: '16bitInt',
        channels: 2,
        sampleRate: 48000,
        flushingTime: 100
      })
      audioWs.binaryType = 'arraybuffer'
      audioWs.onclose = function () {
        console.log('onclose', arguments)
      }
      audioWs.onerror = function () {
        console.log('onerror', arguments)
      }
      audioWs.onmessage = function (message) {
        // console.log(message)
        // var blob = new Blob([message.data])
        var data = new Uint16Array(message.data)
        // console.log(data)
        player.feed(data)
      }
      audioWs.onopen = function () {
        console.log('onopen')
      }
    },
    start () {
      console.log('start')
      var BLANK_IMG = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
      var canvas = document.getElementById('canvas')
      this.canvas = canvas
      this.mouseDownListenStart()
      this.mouseUpListenStart()
      var g = canvas.getContext('2d')
      //   var ws = new WebSocket('ws://127.0.0.1:9002', 'minicap')
      var ws = new WebSocket('ws://127.0.0.1:9002/')
      this.ws = ws
      ws.binaryType = 'blob'
      ws.onclose = function () {
        console.log('onclose', arguments)
      }
      ws.onerror = function () {
        console.log('onerror', arguments)
      }
      ws.onmessage = function (message) {
        var blob = new Blob([message.data], {type: 'image/jpeg'})
        var URL = window.URL || window.webkitURL
        var img = new Image()
        img.onload = function () {
          console.log(img.width, img.height)
          canvas.width = img.width
          canvas.height = img.height
          g.drawImage(img, 0, 0)
          img.onload = null
          img.src = BLANK_IMG
          img = null
          u = null
          blob = null
        }
        var u = URL.createObjectURL(blob)
        img.src = u
        // ws.send('ok')
      }
      ws.onopen = function () {
        console.log('onopen', arguments)
        ws.send('1920x1080/0')
      }
    },
    mouseDownListenStart () {
      this.canvas.addEventListener('mousedown', this.mouseDownMethod)
    },
    mouseDownMethod (e) {
      this.mouseMoveListenStart()
      // console.log('this is mousedown')
      const pos = {
        msg_type: 2,
        msg_inject_touch_action: 0,
        msg_inject_touch_position: {
          x: e.offsetX, y: e.offsetY, width: this.canvas.width, height: this.canvas.height
        }
      }
      // console.log('send data')

      this.ws.send(JSON.stringify(pos))
      // console.log(pos)
    },
    mouseUpListenStart () {
      this.canvas.addEventListener('mouseup', (e) => {
        this.mouseMoveListenEnd()
        // console.log('this is mouseup')
        const pos = {
          msg_type: 2,
          msg_inject_touch_action: 1,
          msg_inject_touch_position: {
            x: e.offsetX, y: e.offsetY, width: this.canvas.width, height: this.canvas.height
          }
        }
        // console.log(e)
        this.ws.send(JSON.stringify(pos))
      })
    },
    mouseMoveListenStart () {
      this.canvas.addEventListener('mousemove', this.mouseMoveMethod)
    },
    mouseMoveMethod (e) {
      // console.log('this is mousemove')
      const pos = {
        msg_type: 2,
        msg_inject_touch_action: 2,
        msg_inject_touch_position: {
          x: e.offsetX, y: e.offsetY, width: this.canvas.width, height: this.canvas.height
        }
      }
      // console.log(pos)
      this.ws.send(JSON.stringify(pos))
    },
    mouseMoveListenEnd () {
      // console.log('remove')
      this.canvas.removeEventListener('mousemove', this.mouseMoveMethod)
    }
  }
}
</script>
