#ifndef GPRN_H
#define GPRN_H

#include "Data.h"
#include "RVmodel.h"
#include "DNest4.h"
#include "RNG.h"

#include <string>
#include <Eigen/Core>
#include <Eigen/Dense>


class GPRN
{
    public:
        GPRN();
        //Eigen::MatrixXd matrixCalculation(std::vector<double> vec1, std::vector<double> vec2);
        std::vector<Eigen::MatrixXd> matrixCalculation(std::vector<double> vec1, std::vector<double> vec2);
        Eigen::MatrixXd nodeCheck(std::string check, std::vector<double> vec1, double sigmaPrior);
        Eigen::VectorXd weightCheck(std::string check, std::vector<double> vec2);


    private:
        double extra_sigma;
        //block matrices
        Eigen::MatrixXd k {Data::get_instance().get_t().size(), Data::get_instance().get_t().size()};
        //comes from main.cpp
        DNest4::ModifiedLogUniform sigmaPrior;
        //comes from main.cpp
        std::vector<std::string> node;
        //comes from main.cpp
        std::vector<std::string> weight;
        //might be smarter to put it in RVmodel.cpp
        std::vector<std::string> weights;
        //node we are working with
        Eigen::MatrixXd nkernel;
        //weight we are working with
        Eigen::VectorXd wkernel;
        //math between weight and node
        Eigen::MatrixXd wn;
        Eigen::MatrixXd wnw;


    //Singleton
    public:
        static GPRN& get_instance() {return instance; }
    private:
        static GPRN instance;
};

#endif // GPRN_H
