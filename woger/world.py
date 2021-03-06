from math import pi
from random import randint, uniform
import random

from pymunk import init_pymunk, Space

from items import BoundingTrunk, CollisionType, Ground, Branch, Bough, Woger, Owange, TopTrunk, Cherry


from sounds import Sounds

from pygame import time, event

import random
NUM_OWANGES = 6

def populate(world, window):
    ground = Ground()
    world.add_item(ground)

    world.add_item(BoundingTrunk(-window.width/2-60))
    world.add_item(BoundingTrunk(window.width/2-10))
    world.add_item(TopTrunk(window.height))
    first = True
    def add_branch(parent, angle, thickness, length, y = None):
        if y is None:
            branch = Branch(parent, angle, thickness, length)
        else:
            branch = Branch(parent, angle, thickness, length, y = y)

        world.add_item(branch)

        if thickness < 25:
            bough = Bough(branch)
            world.add_item(bough)
        else:
            branches = randint(3, 4)
            spread = uniform(pi / 8, pi / branches)
            for i in xrange(branches):
                delta_angle = spread * (branches - 1) / 2 - spread * i
                newangle = angle + delta_angle
                newlength = length * (1 - abs(delta_angle) / 2.8)
                newthickness = thickness * 0.75
                add_branch( branch, newangle, newthickness, newlength)
        return branch

    trunk = add_branch(ground, 0, 50, 220, y = 20)

    woger = Woger(0, 25, window)
    world.add_item(woger)
    world.player_character = woger


    def landed_on_ground(space, arbiter, woger):
        woger.in_air = False
        woger.allowed_glide = 20
        woger.body.reset_forces()

        return 1
    def off_ground(space, arbiter, woger):
        woger.in_air = False
        Sounds.sounds.play("hit1")
        return 1


    def touch_leaf(space, arbiter, woger):
        woger.in_air = True
        woger.allowed_glide = 20
        return 1
    def off_leaf(space, arbiter, woger):
        woger.in_air = True
        Sounds.sounds.play("hit1")
        return 1    

    def touch_cherry(space, arbiter, woger):
        ''' when woger hits a cherry.
        '''
        cherries = [s.parent for s in arbiter.shapes
                      if hasattr(s, 'parent') and isinstance(s.parent, Cherry)]

        for cherry in cherries:
            if cherry.status == "Collided":
                pass
            else:
                woger.multiplier += 1
                Sounds.sounds.play("powerup1")
                world.remove_item(cherry)
        return 1
       

    bounds = window.width
    def touch_owange(space, arbiter, woger):
        ''' when woger hits an owange.
        '''
        owanges = [s.parent for s in arbiter.shapes 
                      if hasattr(s, 'parent') and isinstance(s.parent, Owange)]

        for o in owanges:
            if o.status == "Collided":
                pass
            else:
                woger.score += 10*woger.multiplier
                #Sounds.sounds.play(random.choice(['powerup1', 'goal1']))
                Sounds.sounds.play(random.choice(['goal1']))
                world.remove_item(o)
                # add owange from the top again.
                world.add_owange( randint(-bounds/2, bounds/2), window.height-200) 
        return 1
    def off_owange(space, arbiter, woger):
        return 1    


    def owange_hit_ground(space, arbiter, woger):

        owanges = [s.parent for s in arbiter.shapes 
                      if hasattr(s, 'parent') and isinstance(s.parent, Owange)]
        grounds = [s.parent for s in arbiter.shapes 
                      if hasattr(s, 'parent') and isinstance(s.parent, Ground)]
        if not grounds:
            # must have collided with a leaf?
            return 1
        for o in owanges:
            if o.status != "Collided":
                woger.score -= 2
                Sounds.sounds.play("orange_splat2")
                o.destroy()
                # add owange from the top again.
                #world.add_owange( randint(-bounds/2, bounds/2), window.height-200) 


        return 1
    def owange_off_ground(space, arbiter, woger):
        return 1
   

    def leaf_hit_ground(space, arbiter, woger):
        boughs = [s.parent for s in arbiter.shapes 
                      if hasattr(s, 'parent') and isinstance(s.parent, Bough)]
        grounds = [s.parent for s in arbiter.shapes 
                      if hasattr(s, 'parent') and isinstance(s.parent, Ground)]
        if not grounds:
            # must have collided with a leaf?
            return 1
        for leaf in boughs:
            #print "Destroying"
            leaf.destroy()
            #print leaf.status
        return 1

    def cherry_hit_ground(space, arbiter, woger):
        cherries = [s.parent for s in arbiter.shapes 
                      if hasattr(s, 'parent') and isinstance(s.parent, Cherry)]
        grounds = [s.parent for s in arbiter.shapes 
                      if hasattr(s, 'parent') and isinstance(s.parent, Ground)]
        if not grounds:
            # must have collided with a leaf?
            return 1
#        print cherries
        for cherry in cherries:
            cherry.destroy()
        return 1


    

    world.add_collision_handler(CollisionType.GROUND, CollisionType.PLAYER,
                                begin=landed_on_ground, 
                                separate=off_ground, woger=woger)
    
    world.add_collision_handler(CollisionType.BOUGH, CollisionType.PLAYER,
                                begin=touch_leaf, 
                                separate=off_leaf, woger=woger)
    
    world.add_collision_handler(CollisionType.OWANGE, CollisionType.PLAYER,
                                begin=touch_owange, 
                                separate=off_owange, woger=woger)
    
    world.add_collision_handler(CollisionType.GROUND, CollisionType.OWANGE,
                                begin=owange_hit_ground, 
                                separate=owange_off_ground, woger=woger)

    world.add_collision_handler(CollisionType.GROUND, CollisionType.BOUGH,
                                begin=leaf_hit_ground, separate=None, woger=woger)

    world.add_collision_handler(CollisionType.GROUND, CollisionType.CHERRY,
                                begin=cherry_hit_ground, separate=None, woger=woger)

    world.add_collision_handler(CollisionType.CHERRY, CollisionType.PLAYER,
                                begin=touch_cherry, separate=None, woger=woger)

class World(object):

    def __init__(self):
        self.items = []
        init_pymunk()
        self.space = Space()
        self.space.gravity = (0, -0.5)
        self.space.resize_static_hash()
        self.space.resize_active_hash()
        self.leaves = []
        self.end_game = False
        

    def add_item(self, item):
        if isinstance(item, Bough):
            self.leaves.append(item)
        self.items.append(item)
        item.create_body()
        item.add_to_space(self.space)

    def remove_item(self, item):
        self.items.remove(item)
        item.remove_from_space(self.space)


    def update(self):
        self.space.step(0.5)
        for item in self.items:
            item.update()

    def remove_collided(self):
        for item in self.items:
            if item.status == "Collided":
                self.remove_item(item)
            
    def tick(self):
        max_limit = len(self.leaves) - 1
        if len(self.leaves) == 0:
                max_limit = 0 
##                print "End Level"
                self.end_game = True

        else:
##            print max_limit
            randno = random.randint(0, max_limit)
##            print randno
            leaf = self.leaves.pop(randno)
##            print leaf
            leaf.remove_from_tree(self.space)

    def add_cherry(self, x, y):
        cherry = Cherry(x, y)
        self.add_item(cherry)

    def add_owange(self, x, y):
        owange = Owange(x, y)
        self.add_item(owange)



    def add_collision_handler( self, 
                               col_typ1, 
                               col_typ2, 
                               begin=None, 
                               pre_solve=None,
                               post_solve=None, 
                               separate=None, 
                               **kwargs
        ):
        self.space.add_collision_handler(
            col_typ1, col_typ2,
            begin, pre_solve,
            post_solve, separate,
            **kwargs)
