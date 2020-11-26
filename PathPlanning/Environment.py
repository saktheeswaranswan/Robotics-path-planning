"""
Alonso Vega
October 29, 2020
Environment Class
"""
import Robot
import Tree
import Utility as util

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import collections as pltC
from matplotlib import patches
import Camera


class Environment:
    __slots__ = '_xMin', '_xMax', '_yMin', '_yMax',\
                '_obstacleList',\
                '_goal', '_start', \
                '_axes', '_figure', \
                '_robot', '_RRTtree', \
                '_cov_matrix', \
                '_kd_Tree', \
                '_xTilda', '_camera', \
                '_dt_head_min_pph', '_dt_head_max_pph', '_μ_tHeadControl_pph', '_Σ_tHeadControl_pph', \
                '_Δ_trajectory', '_odeIterGuassMax', '_odeIterMax', \
                '_headSD_Guass'

    def __init__(self, X, Y, obstacle_list, start, goal):
        self._xMin = X[0]
        self._xMax = X[1]

        self._yMin = Y[0]
        self._yMax = Y[1]

        self._obstacleList = obstacle_list

        start = np.array(start)         # initial positional state
        goal  = np.array(goal)          # reference positional state
        self._robot = Robot.Robot(np.concatenate((start, [0, 0, 0])),
                                  q_ref=np.concatenate((start, [0])),
                                  t_1=0.0, t_2=5.0, step_number=500)

        self._RRTtree = Tree.Tree(start)

        self._goal  = goal
        self._start = start

        self._cov_matrix = np.diag([1.5, 1.5])

        self._figure, self._axes = plt.subplots()
        self._figure.set_figheight(5.0)
        self._figure.set_figwidth(5.0)
        self._axes.grid(True)

        self._camera = Camera.Camera(self._figure)

        self._dt_head_min_pph    = 25  # pph
        self._dt_head_max_pph    = 50  # pph
        self._μ_tHeadControl_pph = np.array([10, 25])/100  # pph in decimal
        self._Σ_tHeadControl_pph = np.array([5, 10])/100   # pph in decimal

        self._xTilda = []
        self._Δ_trajectory = 5
        self._odeIterGuassMax = 4       # actual number of normal control calls is one less than this number
        self._odeIterMax      = 6

        self._headSD_Guass = 0.1

    def get_camera(self):
        return self._camera

    def get_robot(self):
        return self._robot

    def x_max(self):
        return self._xMax

    def y_max(self):
        return self._yMax

    def x_min(self):
        return self._xMin

    def y_min(self):
        return self._yMin

    def goal(self):
        return self._goal

    def start(self):
        return self._start

    def set_goal(self, new_goal):
        self._goal = new_goal

    def set_start(self, new_initial_state):
        self._start = new_initial_state

    def obstacles(self):
        return self._obstacleList

    def print_environment(self):

        O_points = []
        limit = 1
        O_points.append([self._xMin, self._yMin])
        O_points.append([self._xMin - limit, self._yMin - limit])
        O_points.append([self._xMin - limit, self._yMax + limit])
        O_points.append([self._xMax + limit, self._yMax + limit])
        O_points.append([self._xMax, self._yMax])
        O_points.append([self._xMin, self._yMax])
        O_points.append([self._xMin, self._yMin])
        O_points = np.array(O_points)
        self._axes.fill(O_points[:, 0], O_points[:, 1], color=(0, 0, 0, 0.15))
        O_points = []
        O_points.append([self._xMin, self._yMin])
        O_points.append([self._xMin - limit, self._yMin - limit])
        O_points.append([self._xMax + limit, self._yMin - limit])
        O_points.append([self._xMax + limit, self._yMax + limit])
        O_points.append([self._xMax, self._yMax])
        O_points.append([self._xMax, self._yMin])
        O_points.append([self._xMin, self._yMin])
        O_points = np.array(O_points)
        self._axes.fill(O_points[:, 0], O_points[:, 1], color=(0, 0, 0, 0.15))

        points = []
        i_1 = 0
        for obstacle in self._obstacleList:
            O_points = []
            for v in obstacle.boundary_vertices():
                x = v.x_value()
                y = v.y_value()
                points.append([x, y])
                O_points.append([x, y])
                self._axes.annotate('v_' + f'{i_1}' + '' + f'{v.id()}', (x, y),
                              (0.65*x + 0.35*obstacle.centroid()[0], 0.65*y + 0.35*obstacle.centroid()[1]))
            O_points = np.array(O_points)
            self._axes.fill(O_points[:, 0], O_points[:, 1], color=(0, 0, 0, 0.15))
            i_1 = i_1 + 1
        points = np.array(points)
        self._axes.scatter(points[:, 0], points[:, 1], s=30.0, color=(0, 0, 1, 0.5))

        points = []
        i_1 = 0
        for obstacle in self._obstacleList:
            O_cent = obstacle.centroid()
            points.append(O_cent)
            self._axes.annotate('O_' + f'{i_1}', (O_cent[0], O_cent[1]))
            i_1 = i_1 + 1
        points = np.array(points)
        self._axes.scatter(points[:, 0], points[:, 1],
                     s=100.0, color=(0, 0, 0, 0.2), marker='h')

        points = []
        for obstacle in self._obstacleList:
            for e in obstacle.edges():
                (v_1, v_2) = e.end_vertices()
                points.append([(v_1.x_value(), v_1.y_value()), (v_2.x_value(), v_2.y_value())])
        points.append([(self._xMin, self._yMin), (self._xMin, self._yMax)])
        points.append([(self._xMin, self._yMax), (self._xMax, self._yMax)])
        points.append([(self._xMax, self._yMax), (self._xMax, self._yMin)])
        points.append([(self._xMax, self._yMin), (self._xMin, self._yMin)])

        segments = pltC.LineCollection(points, linewidths=0.75, colors=(0, 0, 1, 1))
        self._axes.add_collection(segments)

        self._axes.scatter(self._goal[0], self._goal[1], s=900.0, color=(0.5, 0.25, 0.15, 0.1), marker='o')

        self._axes.set_xlim(self._xMin - limit, self._xMax + limit)
        self._axes.set_ylim(self._yMin - limit, self._yMax + limit)

    def axes(self):
        return self._axes

    def figure(self):
        return self._figure

    def collision(self, point):
        point = np.array(point)
        col_vect = (point < np.array([self._xMin, self._yMin])) \
                   | (np.isclose(point, [self._xMin, self._yMin], atol=0.1, rtol=0.0))\
                   | (point > np.array([self._xMax, self._yMax]))\
                   | (np.isclose(point, [self._xMax, self._yMax], atol=0.1, rtol=0.0))
        collision = (col_vect[0] | col_vect[1])
        if collision:
            return True

        for obstacle in self._obstacleList:
            col_vect = np.matmul(obstacle.boundary()['N'], point) + obstacle.boundary()['b']
            col_vect = (col_vect < 0) | (np.isclose(col_vect, np.zeros(len(col_vect)), atol=1.0e-5, rtol=1.0e-5))
            collision = (np.sum(col_vect.astype(int)) == len(col_vect))
            if collision:
                return True
        return False

    def sample(self, n, distribution):
        if distribution == 'U':
            x_rand = np.random.uniform(self._xMin, self._xMax, n)
            y_rand = np.random.uniform(self._yMin, self._yMax, n)
        elif distribution == 'N':
            q_0 = self._robot.get_x_0()[0:3]
            r_0 = util.polar2xy(q_0)

            Σ = self._cov_matrix
            μ = np.array([r_0[0], r_0[1]])

            sample = np.random.multivariate_normal(μ, Σ, n)
            x_rand = sample[:, 0]
            y_rand = sample[:, 1]
        else:
            print('\nERROR: no such distribution.\n')

        color = []
        for i in range(0, len(x_rand)):
            collision = self.collision([x_rand[i], y_rand[i]])
            if collision:
                color.append((1.0, 0.0, 0.0, 1.0))
            else:
                color.append((0.4, 0.75, 0.1, 1.0))

        self._axes.scatter(x_rand, y_rand,
                           s=10.00, color=color, marker='o')
        return x_rand, y_rand

    # ________________________________________________Integration_______________________________________________________
    def draw_robot_trajectory(self, plot=False):
        (self._xTilda, info) = self._robot.get_trajectory(degrees=False, plot=plot)

        odeIterGuassMax = self._odeIterGuassMax
        odeIterMax      = self._odeIterMax
        ode_iter = 1
        while info['message'] != 'Integration successful.':
            if ode_iter < odeIterGuassMax:
                (t_head_min, t_head_max) = self.set_random_time_control('N')
                print('\nChanging Control: Normal heading time control: (', t_head_min, ',', t_head_max, ')')
            else:
                if (ode_iter + 1) == odeIterMax:
                    (t_head_min, t_head_max) = self._robot.get_time_duration()
                    self._robot.set_t_head_max(t_head_max)
                    self._robot.set_t_head_min(t_head_min)
                    print('\nChanging Control: Full heading time control: (', t_head_min, ',', t_head_max, ')')
                else:
                    (t_head_min, t_head_max) = self.set_random_time_control('U')
                    print('\nChanging Control: Uniform heading time control: (', t_head_min, ',', t_head_max, ')')

            ode_iter = ode_iter + 1
            print('ERROR: integration failed, trying again. Iteration:', ode_iter, ' \n')
            (self._xTilda, info) = self._robot.get_trajectory(degrees=False, plot=plot)

            if ode_iter >= odeIterMax:
                if info['message'] != 'Integration successful.':
                    print('\nERROR: integration failed, max iterations reached. Total Iteration:', ode_iter, ' \n')
                    return info['message']
                else:
                    break
        print('\nIntegration successful after ', ode_iter, ' iterations. \n')

        r_cTilda = self._xTilda[:, 0:2]
        (x_c, y_c) = util.polar2xy_large(r_cTilda)

        self._axes.plot(x_c, y_c)
        return info['message']
    # ________________________________________________Integration_______________________________________________________

    def play_robot_trajectory(self):
        xTilda     = self._xTilda
        (t_1, t_2) = self._robot.get_time_duration()
        N          = self._robot.get_number_time_steps()
        Δt         = (t_2 - t_1)/N
        Δt         = Δt*1000            # [ms]

        for i in range(0, len(xTilda[:, 1])):
            self.animate(i)

        anime = self._camera.animate()
        return anime

    def animate(self, i):
        xTilda = self._xTilda
        q_cTilda   = xTilda[:, 0:3]
        (x_c, y_c) = util.polar2xy_large(q_cTilda)

        r_c = np.array([x_c[i], y_c[i]])
        θ_c = q_cTilda[i, 2]

        R       = self._robot.get_wheel_radius()
        R_robot = self._robot.get_base_radius()
        l       = self._robot.get_wheel_center_distance()

        wheel_rightFront = r_c + np.matmul(np.diag([1, -1]), l * util.SC_vect(θ_c)) \
                               + np.matmul(np.diag([1, 1]), R * util.CS_vect(θ_c))
        wheel_rightBack  = r_c + np.matmul(np.diag([1, -1]), l * util.SC_vect(θ_c)) \
                               + np.matmul(np.diag([-1, -1]), R * util.CS_vect(θ_c))
        wheel_leftFront  = r_c + np.matmul(np.diag([-1, 1]), l * util.SC_vect(θ_c)) \
                               + np.matmul(np.diag([1, 1]), R * util.CS_vect(θ_c))
        wheel_leftBack   = r_c + np.matmul(np.diag([-1, 1]), l * util.SC_vect(θ_c)) \
                               + np.matmul(np.diag([-1, -1]), R * util.CS_vect(θ_c))

        head_right  = r_c + np.matmul(np.diag([1, -1]), l * util.SC_vect(θ_c))
        head_left   = r_c + np.matmul(np.diag([-1, 1]), l * util.SC_vect(θ_c))
        head_center = r_c + R_robot*util.CS_vect(θ_c)

        head       = [[head_left, head_center],
                      [head_right, head_center],
                      [head_left, head_right]]
        head_color = np.array([(0.0, 0.0, 0.0, 0.8), (0.0, 0.1, 0.0, 0.8), (0.6, 0.1, 0.2, 0.8)])
        head_art = pltC.LineCollection(head, colors=(0.0, 0.1, 0.0, 0.8), linewidths=1.0)

        wheels = [[wheel_leftBack, wheel_leftFront],
                  [wheel_rightBack, wheel_rightFront]]
        wheel_color = np.array([(0, 0, 0, 0.85), (0, 0, 0, 0.85)])
        wheel_art = pltC.LineCollection(wheels, colors=wheel_color, linewidths=4)

        base1 = patches.Circle((r_c[0], r_c[1]),
                               R_robot,
                               color=(1.0, 0.0, 0.0, 0.7))
        base2 = patches.Circle((r_c[0], r_c[1]),
                               0.70 * R_robot,
                               color=(0.3, 0.7, 1.0, 1.0))

        wheel_art.set_zorder(0)
        base1.set_zorder(5)
        base2.set_zorder(10)
        head_art.set_zorder(20)

        art_1 = self._axes.add_collection(wheel_art)
        art_2 = self._axes.add_artist(base1)
        art_3 = self._axes.add_artist(base2)
        art_4 = self._axes.add_collection(head_art)
        art_list = [art_1, art_2, art_3, art_4]

        self._camera.snap(art_list)

    def refresh_figure(self):
        self._figure.show()

    def set_random_time_control(self, distribution='U'):
        (t_1, t_2) = self._robot.get_time_duration()
        dura = t_2 - t_1
        dt_min = (self._dt_head_min_pph / 100) * dura
        dt_max = (self._dt_head_max_pph / 100) * dura

        while True:
            if distribution == 'U':
                t_head_min = np.random.uniform(t_1, t_2)
                t_head_max = np.random.uniform(t_1, t_2)
            elif distribution == 'N':
                μ_tHeadControl_pph = self._μ_tHeadControl_pph
                Σ_tHeadControl_pph = self._Σ_tHeadControl_pph

                (μ_tMin, Σ_tMin)  = (np.array(μ_tHeadControl_pph)*dura,
                                     np.diag(Σ_tHeadControl_pph)*dura)

                t_head = np.random.multivariate_normal(μ_tMin, Σ_tMin, 1)
                t_head_min = t_head[0][0]
                t_head_max = t_head[0][1]
            else:
                print('\nERROR: no such distribution.\n')

            dt = t_head_max - t_head_min
            if (dt > dt_min) & (dt < dt_max) & (t_head_max >= 0) & (t_head_min >= 0):
                break

        self._robot.set_t_head_max(t_head_max)
        self._robot.set_t_head_min(t_head_min)
        return t_head_min, t_head_max

    def collision_trajectory(self, plot=False):
        r_cTilda   = self._xTilda[:, 0:2]
        (x_c, y_c) = util.polar2xy_large(r_cTilda)

        Δ_trajectory = self._Δ_trajectory

        x_c_approx = []
        y_c_approx = []
        for i in range(0, len(x_c), Δ_trajectory):
            x_c_approx.append(x_c[i])
            y_c_approx.append(y_c[i])

        if plot:
            for i in range(0, len(x_c_approx)):
                self._axes.scatter(x_c_approx[i], y_c_approx[i], s=10.0, color=(1, 0, 0, 1.0))

        for i in range(0, len(x_c_approx)):
            r_cTilda_approx_i = np.array([x_c_approx[i],
                                          y_c_approx[i]])
            collision_i = self.collision(r_cTilda_approx_i)
            if collision_i:
                return True

        return False

    def sample_angle(self, n, distribution='U'):
        if distribution == 'U':
            θ_rand = np.random.uniform(-np.pi, np.pi, n)
        elif distribution == 'N':
            μ, σ = self._robot.get_x_0()[3], self._headSD_Guass  # mean and standard deviation
            θ_rand = np.random.normal(μ, σ, n)
        else:
            print('\nERROR: no such distribution.\n')

        return θ_rand

    def random_config(self, n, distribution='U'):
        (x_rand, y_rand) = self.sample(n, distribution)
        θ_rand           = self.sample_angle(n, distribution)

        (ρ_rand, φ_rand) = util.xy2polar(x_rand, y_rand)
        q_rand = np.array([ρ_rand, φ_rand, θ_rand])
        return q_rand

    def new_state(self, q_rand, q_near):
        self.draw_robot_trajectory(plot=False)



        return 0


    """"
    # _______________________________________________RRT___________________________________________________________
    def build_RRT(self, K):
        for k in range(0, K+1):
            x_rand = self.random_state()
            self.extend_tree(x_rand)

    

    def extend_tree(self, x_rand):
        x_near = self.nearest_neighbor(q_rand)
        if new_state(x_rand, x_near):
            self._RRTtree.insert_vertex(xCoord_new, yCoord_new, v_near, element=x_new)
            self._RRTtree.insert_edge(v_near, v_new, x=None)

            if x_new == x_rand:
                return 'reached'
            else:
                return 'advanced'

        return 'trapped'

    def nearest_neighbor(self, x_rand, exact):
        if (exact):
            naviee way 
        else:
            kd tree way 
        
        return 0

    
    # _______________________________________________RRT___________________________________________________________
    #"""





