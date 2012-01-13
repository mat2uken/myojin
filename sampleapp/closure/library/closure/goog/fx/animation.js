// Copyright 2006 The Closure Library Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Classes for doing animations and visual effects.
 *
 * (Based loosly on my animation code for 13thparallel.org, with extra
 * inspiration from the DojoToolkit's modifications to my code)
 */

goog.provide('goog.fx.Animation');
goog.provide('goog.fx.Animation.EventType');
goog.provide('goog.fx.Animation.State');
goog.provide('goog.fx.AnimationEvent');

goog.require('goog.Timer');
goog.require('goog.array');
goog.require('goog.events.Event');
goog.require('goog.events.EventTarget');
goog.require('goog.fx.Transition');  // Unreferenced: interface
goog.require('goog.fx.Transition.EventType');
goog.require('goog.object');



/**
 * Constructor for an animation object.
 * @param {Array.<number>} start Array for start coordinates.
 * @param {Array.<number>} end Array for end coordinates.
 * @param {number} duration Length of animation in milliseconds.
 * @param {Function=} opt_acc Acceleration function, returns 0-1 for inputs 0-1.
 * @constructor
 * @implements {goog.fx.Transition}
 * @extends {goog.events.EventTarget}
 */
goog.fx.Animation = function(start, end, duration, opt_acc) {
  goog.events.EventTarget.call(this);

  if (!goog.isArray(start) || !goog.isArray(end)) {
    throw Error('Start and end parameters must be arrays');
  }

  if (start.length != end.length) {
    throw Error('Start and end points must be the same length');
  }

  /**
   * Start point.
   * @type {Array.<number>}
   * @protected
   */
  this.startPoint = start;

  /**
   * End point.
   * @type {Array.<number>}
   * @protected
   */
  this.endPoint = end;

  /**
   * Duration of animation in milliseconds.
   * @type {number}
   * @protected
   */
  this.duration = duration;

  /**
   * Acceleration function, which must return a number between 0 and 1 for
   * inputs between 0 and 1.
   * @type {Function|undefined}
   * @private
   */
  this.accel_ = opt_acc;

  /**
   * Current coordinate for animation.
   * @type {Array.<number>}
   * @protected
   */
  this.coords = [];
};
goog.inherits(goog.fx.Animation, goog.events.EventTarget);


/**
 * Events fired by the animation.
 * @enum {string}
 */
goog.fx.Animation.EventType = {
  /**
   * Dispatched when played for the first time OR when it is resumed.
   * @deprecated Use goog.fx.Transition.EventType.PLAY.
   */
  PLAY: goog.fx.Transition.EventType.PLAY,

  /**
   * Dispatched only when the animation starts from the beginning.
   * @deprecated Use goog.fx.Transition.EventType.BEGIN.
   */
  BEGIN: goog.fx.Transition.EventType.BEGIN,

  /**
   * Dispatched only when animation is restarted after a pause.
   * @deprecated Use goog.fx.Transition.EventType.RESUME.
   */
  RESUME: goog.fx.Transition.EventType.RESUME,

  /**
   * Dispatched when animation comes to the end of its duration OR stop
   * is called.
   * @deprecated Use goog.fx.Transition.EventType.END.
   */
  END: goog.fx.Transition.EventType.END,

  /**
   * Dispatched only when stop is called.
   * @deprecated Use goog.fx.Transition.EventType.STOP.
   */
  STOP: goog.fx.Transition.EventType.STOP,

  /**
   * Dispatched only when animation comes to its end naturally.
   * @deprecated Use goog.fx.Transition.EventType.FINISH.
   */
  FINISH: goog.fx.Transition.EventType.FINISH,

  /**
   * Dispatched when an animation is paused.
   * @deprecated Use goog.fx.Transition.EventType.PAUSE.
   */
  PAUSE: goog.fx.Transition.EventType.PAUSE,

  /**
   * Dispatched each frame of the animation.  This is where the actual animator
   * will listen.
   */
  ANIMATE: 'animate',

  /**
   * Dispatched when the animation is destroyed.
   */
  DESTROY: 'destroy'
};


/**
 * Enum for the possible states of an animation.
 * @enum {number}
 */
goog.fx.Animation.State = {
  STOPPED: 0,
  PAUSED: -1,
  PLAYING: 1
};


/**
 * Default timeout for animations (in milliseconds).
 * @type {number}
 */
goog.fx.Animation.TIMEOUT = 20;


/**
 * A map of animations which should be cycled on the global timer.
 * @type {Object}
 * @private
 */
goog.fx.Animation.activeAnimations_ = {};


/**
 * An interval ID for the global timer.
 * @type {?number}
 * @private
 */
goog.fx.Animation.globalTimer_ = null;


/**
 * An optional animation window.
 * @type {?Window}
 * @private
 */
goog.fx.Animation.animationWindow_ = null;


/**
 * A timing control function.
 * @type {?function(function(number))}
 * @private
 */
goog.fx.Animation.requestAnimationFrameFn_ = null;


/**
 * Cancel function for timing control.
 * @type {?function(number)}
 * @private
 */
goog.fx.Animation.cancelRequestAnimationFrameFn_ = null;


/**
 * Cycle all registered animations.
 * @private
 */
goog.fx.Animation.cycleAnimations_ = function() {
  goog.fx.Animation.resetTimer_();

  // Cycle all animations at the "same time".
  var now = goog.now();

  for (var uid in goog.fx.Animation.activeAnimations_) {
    goog.fx.Animation.activeAnimations_[uid].cycle(now);
  }

  goog.fx.Animation.globalTimer_ =
      goog.object.isEmpty(goog.fx.Animation.activeAnimations_) ?
          null :
          goog.fx.Animation.startTimer_();
};


/**
 * Resets the animation timer.
 * @private
 */
goog.fx.Animation.resetTimer_ = function() {
  if (goog.fx.Animation.globalTimer_) {
    if (goog.fx.Animation.requestAnimationFrameFn_) {
      goog.fx.Animation.cancelRequestAnimationFrameFn_.call(
          goog.fx.Animation.animationWindow_,
          goog.fx.Animation.globalTimer_);
    } else {
      goog.Timer.defaultTimerObject.clearTimeout(
          goog.fx.Animation.globalTimer_);
    }
    goog.fx.Animation.globalTimer_ = null;
  }
};


/**
 * Starts the animation timer.
 * @return {number} A unique ID for the timer, that can be used to clear it.
 * @private
 */
goog.fx.Animation.startTimer_ = function() {
  if (goog.fx.Animation.requestAnimationFrameFn_) {
    return goog.fx.Animation.requestAnimationFrameFn_.call(
        goog.fx.Animation.animationWindow_,
        goog.fx.Animation.cycleAnimations_);
  }
  return goog.Timer.defaultTimerObject.setTimeout(
      goog.fx.Animation.cycleAnimations_, goog.fx.Animation.TIMEOUT);
};


/**
 * Register an animation to be cycled on the global timer.
 * @param {Object} animation The animation to register.
 */
goog.fx.Animation.registerAnimation = function(animation) {
  var uid = goog.getUid(animation);
  if (!(uid in goog.fx.Animation.activeAnimations_)) {
    goog.fx.Animation.activeAnimations_[uid] = animation;
  }

  // If the timer is not already started, start it now.
  if (!goog.fx.Animation.globalTimer_) {
    goog.fx.Animation.globalTimer_ = goog.fx.Animation.startTimer_();
  }
};


/**
 * Remove an animation from the list of animations which are cycled on the
 * global timer.
 * @param {Object} animation The animation to unregister.
 */
goog.fx.Animation.unregisterAnimation = function(animation) {
  var uid = goog.getUid(animation);
  delete goog.fx.Animation.activeAnimations_[uid];

  // If a timer is running and we no longer have any active timers we stop the
  // timers.
  if (goog.object.isEmpty(goog.fx.Animation.activeAnimations_)) {
    goog.fx.Animation.resetTimer_();
  }
};


/**
 * Registers an animation window. This allows usage of the timing control API
 * for animations. Note that this window must be visible, as non-visible
 * windows can potentially stop animating. This window does not necessarily
 * need to be the window inside which animation occurs, but must remain visible.
 * See: https://developer.mozilla.org/en/DOM/window.mozRequestAnimationFrame.
 *
 * @param {Window} animationWindow The window in which to animate elements.
 */
goog.fx.Animation.setAnimationWindow = function(animationWindow) {
  goog.fx.Animation.animationWindow_ = animationWindow;

  if (!animationWindow) {
    goog.fx.Animation.requestAnimationFrameFn_ = null;
    goog.fx.Animation.cancelRequestAnimationFrameFn_ = null;
    return;
  }

  goog.fx.Animation.requestAnimationFrameFn_ =
      animationWindow['requestAnimationFrame'] ||
      animationWindow['webkitRequestAnimationFrame'] ||
      animationWindow['mozRequestAnimationFrame'] ||
      animationWindow['oRequestAnimationFrame'] ||
      animationWindow['msRequestAnimationFrame'];

  goog.fx.Animation.cancelRequestAnimationFrameFn_ =
      animationWindow['cancelRequestAnimationFrame'] ||
      animationWindow['webkitCancelRequestAnimationFrame'] ||
      animationWindow['mozCancelRequestAnimationFrame'] ||
      animationWindow['oCancelRequestAnimationFrame'] ||
      animationWindow['msCancelRequestAnimationFrame'];
};


/**
 * Current state of the animation.
 * @type {goog.fx.Animation.State}
 * @private
 */
goog.fx.Animation.prototype.state_ = goog.fx.Animation.State.STOPPED;


/**
 * Current frame rate.
 * @type {number}
 * @private
 */
goog.fx.Animation.prototype.fps_ = 0;


/**
 * Percent of the way through the animation.
 * @type {number}
 * @protected
 */
goog.fx.Animation.prototype.progress = 0;


/**
 * Timestamp for when animation was started.
 * @type {?number}
 * @protected
 */
goog.fx.Animation.prototype.startTime = null;


/**
 * Timestamp for when animation was started.
 * @type {?number}
 * @protected
 */
goog.fx.Animation.prototype.endTime = null;


/**
 * Timestamp for when last frame was run.
 * @type {?number}
 * @protected
 */
goog.fx.Animation.prototype.lastFrame = null;


/**
 * Gets the animation state.
 * @return {goog.fx.Animation.State} The current state.
 * @protected
 */
goog.fx.Animation.prototype.getStateInternal = function() {
  return this.state_;
};


/**
 * Starts or resumes an animation.
 * @param {boolean=} opt_restart Whether to restart the
 *     animation from the beginning if it has been paused.
 * @return {boolean} Whether animation was started.
 */
goog.fx.Animation.prototype.play = function(opt_restart) {
  if (opt_restart || this.state_ == goog.fx.Animation.State.STOPPED) {
    this.progress = 0;
    this.coords = this.startPoint;
  } else if (this.state_ == goog.fx.Animation.State.PLAYING) {
    return false;
  }

  goog.fx.Animation.unregisterAnimation(this);

  var now = /** @type {number} */ (goog.now());

  this.startTime = now;
  if (this.state_ == goog.fx.Animation.State.PAUSED) {
    this.startTime -= this.duration * this.progress;
  }

  this.endTime = this.startTime + this.duration;
  this.lastFrame = this.startTime;

  if (!this.progress) {
    this.onBegin();
  }

  this.onPlay();

  if (this.state_ == goog.fx.Animation.State.PAUSED) {
    this.onResume();
  }

  this.state_ = goog.fx.Animation.State.PLAYING;

  goog.fx.Animation.registerAnimation(this);
  this.cycle(now);

  return true;
};


/**
 * Stops the animation.
 * @param {boolean} gotoEnd If true the animation will move to the end coords.
 */
goog.fx.Animation.prototype.stop = function(gotoEnd) {
  goog.fx.Animation.unregisterAnimation(this);
  this.state_ = goog.fx.Animation.State.STOPPED;

  if (gotoEnd) {
    this.progress = 1;
  }

  this.updateCoords_(this.progress);

  this.onStop();
  this.onEnd();
};


/**
 * Pauses the animation (iff it's playing).
 */
goog.fx.Animation.prototype.pause = function() {
  if (this.state_ == goog.fx.Animation.State.PLAYING) {
    goog.fx.Animation.unregisterAnimation(this);
    this.state_ = goog.fx.Animation.State.PAUSED;
    this.onPause();
  }
};


/**
 * Sets the progress of the animation.
 * @param {number} progress The new progress of the animation.
 */
goog.fx.Animation.prototype.setProgress = function(progress) {
  this.progress = progress;
  if (this.state_ == goog.fx.Animation.State.PLAYING) {
    var now = goog.now();
    // If the animation is already playing, we recompute startTime and endTime
    // such that the animation plays consistently, that is:
    // now = startTime + progress * duration.
    this.startTime = now - this.duration * this.progress;
    this.endTime = this.startTime + this.duration;
  }
};


/**
 * Disposes of the animation.  Stops an animation, fires a 'destroy' event and
 * then removes all the event handlers to clean up memory.
 * @override
 * @protected
 */
goog.fx.Animation.prototype.disposeInternal = function() {
  if (this.state_ != goog.fx.Animation.State.STOPPED) {
    this.stop(false);
  }
  this.onDestroy();
  goog.fx.Animation.superClass_.disposeInternal.call(this);
};


/**
 * Stops an animation, fires a 'destroy' event and then removes all the event
 * handlers to clean up memory.
 * @deprecated Use dispose() instead.
 */
goog.fx.Animation.prototype.destroy = function() {
  this.dispose();
};


/**
 * Handles the actual iteration of the animation in a timeout
 * @param {number} now The current time.
 */
goog.fx.Animation.prototype.cycle = function(now) {
  this.progress = (now - this.startTime) / (this.endTime - this.startTime);

  if (this.progress >= 1) {
    this.progress = 1;
  }

  this.fps_ = 1000 / (now - this.lastFrame);
  this.lastFrame = now;

  this.updateCoords_(this.progress);

  // Animation has finished.
  if (this.progress == 1) {
    this.state_ = goog.fx.Animation.State.STOPPED;
    goog.fx.Animation.unregisterAnimation(this);

    this.onFinish();
    this.onEnd();

  // Animation is still under way.
  } else if (this.state_ == goog.fx.Animation.State.PLAYING) {
    this.onAnimate();
  }
};


/**
 * Calculates current coordinates, based on the current state.  Applies
 * the accelleration function if it exists.
 * @param {number} t Percentage of the way through the animation as a decimal.
 * @private
 */
goog.fx.Animation.prototype.updateCoords_ = function(t) {
  if (goog.isFunction(this.accel_)) {
    t = this.accel_(t);
  }
  this.coords = new Array(this.startPoint.length);
  for (var i = 0; i < this.startPoint.length; i++) {
    this.coords[i] = (this.endPoint[i] - this.startPoint[i]) * t +
        this.startPoint[i];
  }
};


/**
 * Dispatches the ANIMATE event. Sub classes should override this instead
 * of listening to the event.
 * @protected
 */
goog.fx.Animation.prototype.onAnimate = function() {
  this.dispatchAnimationEvent_(goog.fx.Animation.EventType.ANIMATE);
};


/**
 * Dispatches the BEGIN event. Sub classes should override this instead
 * of listening to the event.
 * @protected
 */
goog.fx.Animation.prototype.onBegin = function() {
  this.dispatchAnimationEvent_(goog.fx.Transition.EventType.BEGIN);
};


/**
 * Dispatches the DESTROY event. Sub classes should override this instead
 * of listening to the event.
 * @protected
 */
goog.fx.Animation.prototype.onDestroy = function() {
  this.dispatchAnimationEvent_(goog.fx.Animation.EventType.DESTROY);
};


/**
 * Dispatches the END event. Sub classes should override this instead
 * of listening to the event.
 * @protected
 */
goog.fx.Animation.prototype.onEnd = function() {
  this.dispatchAnimationEvent_(goog.fx.Transition.EventType.END);
};


/**
 * Dispatches the FINISH event. Sub classes should override this instead
 * of listening to the event.
 * @protected
 */
goog.fx.Animation.prototype.onFinish = function() {
  this.dispatchAnimationEvent_(goog.fx.Transition.EventType.FINISH);
};


/**
 * Dispatches the PAUSE event. Sub classes should override this instead
 * of listening to the event.
 * @protected
 */
goog.fx.Animation.prototype.onPause = function() {
  this.dispatchAnimationEvent_(goog.fx.Transition.EventType.PAUSE);
};


/**
 * Dispatches the PLAY event. Sub classes should override this instead
 * of listening to the event.
 * @protected
 */
goog.fx.Animation.prototype.onPlay = function() {
  this.dispatchAnimationEvent_(goog.fx.Transition.EventType.PLAY);
};


/**
 * Dispatches the RESUME event. Sub classes should override this instead
 * of listening to the event.
 * @protected
 */
goog.fx.Animation.prototype.onResume = function() {
  this.dispatchAnimationEvent_(goog.fx.Transition.EventType.RESUME);
};


/**
 * Dispatches the STOP event. Sub classes should override this instead
 * of listening to the event.
 * @protected
 */
goog.fx.Animation.prototype.onStop = function() {
  this.dispatchAnimationEvent_(goog.fx.Transition.EventType.STOP);
};


/**
 * Returns an event object for the current animation.
 * @param {string} type Event type that will be dispatched.
 * @private
 */
goog.fx.Animation.prototype.dispatchAnimationEvent_ = function(type) {
  this.dispatchEvent(new goog.fx.AnimationEvent(type, this));
};



/**
 * Class for an animation event object.
 * @param {string} type Event type.
 * @param {goog.fx.Animation} anim An animation object.
 * @constructor
 * @extends {goog.events.Event}
 */
goog.fx.AnimationEvent = function(type, anim) {
  goog.events.Event.call(this, type);

  /**
   * The current coordinates.
   * @type {Array.<number>}
   */
  this.coords = anim.coords;

  /**
   * The x coordinate.
   * @type {number}
   */
  this.x = anim.coords[0];

  /**
   * The y coordinate.
   * @type {number}
   */
  this.y = anim.coords[1];

  /**
   * The z coordinate.
   * @type {number}
   */
  this.z = anim.coords[2];

  /**
   * The current duration.
   * @type {number}
   */
  this.duration = anim.duration;

  /**
   * The current progress.
   * @type {number}
   */
  this.progress = anim.progress;

  /**
   * Frames per second so far.
   */
  this.fps = anim.fps_;

  /**
   * The state of the animation.
   * @type {number}
   */
  this.state = anim.state_;

  /**
   * The animation object.
   * @type {goog.fx.Animation}
   */
  // TODO(user): This can be removed as this is the same as the target
  this.anim = anim;
};
goog.inherits(goog.fx.AnimationEvent, goog.events.Event);


/**
 * Returns the coordinates as integers (rounded to nearest integer).
 * @return {Array.<number>} An array of the coordinates rounded to
 *     the nearest integer.
 */
goog.fx.AnimationEvent.prototype.coordsAsInts = function() {
  return goog.array.map(this.coords, Math.round);
};
