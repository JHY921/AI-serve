import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 生成模拟数据
np.random.seed(0)
X = np.random.randint(0, 200, size=(1000, 4))
Y = X[:, 0] * 0.05 + X[:, 1] * 0.03 + X[:, 2] * 0.07 + X[:, 3] * 5 + np.random.randn(1000) * 2


def predict_score(X, Y):
    # 数据归一化/标准化
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # 数据分割: 80% 训练，10% 验证，10% 测试
    X_train, X_temp, Y_train, Y_temp = train_test_split(X, Y, test_size=0.2, random_state=0)
    X_val, X_test, Y_val, Y_test = train_test_split(X_temp, Y_temp, test_size=0.5, random_state=0)

    # 定义模型
    model = Sequential()
    model.add(Dense(64, input_dim=4, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1, activation='linear'))

    # 编译模型
    optimizer = Adam(lr=0.001)
    model.compile(loss='mean_squared_error', optimizer=optimizer)

    # 训练模型
    model.fit(X_train, Y_train, validation_data=(X_val, Y_val), epochs=200, batch_size=32)

    # 模型评估
    loss = model.evaluate(X_test, Y_test, verbose=0)

    # 预测
    sample = np.array([[10, 100, 5, 1]])
    sample = scaler.transform(sample)  # 不要忘记标准化
    predicted_score = model.predict(sample)
    return predicted_score
