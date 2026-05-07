package com.environment.pojo.DTO;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class PageDTO {
    //默认值为1
    private Integer page=1;
    //默认值为10
    private Integer size=10;
    private String role;
}
