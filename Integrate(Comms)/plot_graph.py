import matplotlib.pyplot as plt
import matplotlib
matplotlib.

collected_data = []

plt.close()

for i in range(30):
    collected_data.append([i for _ in range(6)])
    
print(collected_data)
x_axis = [i + 1 for i in range(30)]
roll_list = [collected_data[i][0] for i in range(30)]
pitch_list = [collected_data[i][1] for i in range(30)]
yaw_list = [collected_data[i][2] for i in range(30)]
acc_x_list = [collected_data[i][3] for i in range(30)]
acc_y_list = [collected_data[i][4] for i in range(30)]
acc_z_list = [collected_data[i][5] for i in range(30)]
fig, axs = plt.subplots(2, 3)
axs[0, 0].plot(x_axis, roll_list)
axs[0, 0].set_title('roll graph')
axs[0, 1].plot(x_axis, pitch_list)
axs[0, 1].set_title('pitch graph')
axs[0, 2].plot(x_axis, yaw_list)
axs[0, 2].set_title('yaw graph')
axs[1, 0].plot(x_axis, acc_x_list)
axs[1, 0].set_title('acc_x graph')
axs[1, 1].plot(x_axis, acc_y_list)
axs[1, 1].set_title('acc_y graph')
axs[1, 2].plot(x_axis, acc_z_list)
axs[1, 2].set_title('acc_z graph')

fig.tight_layout(pad=1.5)

for ax in axs.flat:
    ax.set()

plt.plot()